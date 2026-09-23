from datetime import timedelta

from odoo import api, fields, models


class SeyalDashboard(models.AbstractModel):
    _name = "seyal.dashboard"
    _description = "Tableau de bord Direction SEYAL-TCHAD"

    def _readable_env(self, model_name):
        """Sudo fallback per model for roles with no direct read access to it
        (mirrors ste_dashboard's own _readable_env in this repo) : every role
        can open this dashboard menu, but most roles have no direct access
        to, say, seyal.invoice or seyal.expense - granting broad model-level
        read access instead would quietly let them browse those screens
        directly, defeating the separation of duties set up in
        seyal_security/seyal_*'s own ir.model.access.csv files.
        """
        if self.env["ir.model.access"].check(model_name, "read", raise_exception=False):
            return self.env
        return self.sudo().env

    @api.model
    def get_kpis(self):
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)

        invoice_env = self._readable_env("seyal.invoice")["seyal.invoice"]
        invoices_today = invoice_env.search([
            ("state", "=", "validated"), ("move_type", "=", "invoice"), ("invoice_date", "=", today),
        ])
        invoices_month = invoice_env.search([
            ("state", "=", "validated"), ("move_type", "=", "invoice"),
            ("invoice_date", ">=", month_start), ("invoice_date", "<=", today),
        ])
        ca_today = sum(invoices_today.mapped("amount_total"))
        ca_month = sum(invoices_month.mapped("amount_total"))

        order_env = self._readable_env("seyal.sale.order")["seyal.sale.order"]
        orders_month = order_env.search([
            ("state", "in", ("confirmed", "done")),
            ("order_date", ">=", month_start), ("order_date", "<=", today),
        ])
        ventes_count = len(orders_month)
        ventes_amount = sum(orders_month.mapped("amount_total"))

        purchase_env = self._readable_env("seyal.purchase.order")["seyal.purchase.order"]
        purchases_month = purchase_env.search([
            ("state", "in", ("confirmed", "done")),
            ("order_date", ">=", month_start), ("order_date", "<=", today),
        ])
        achats_amount = sum(purchases_month.mapped("amount_total"))

        # Uses invoice_env's (already correctly sudo-or-not) environment
        # rather than its own: this domain traverses invoice_id.state/
        # move_type/invoice_date, and Odoo checks ACL on every model a
        # domain touches via such a join, not just the root model being
        # searched - so sudo status has to follow seyal.invoice here, not
        # seyal.invoice.line's own (broader) access level.
        lines_month = invoice_env.env["seyal.invoice.line"].search([
            ("invoice_id.state", "=", "validated"), ("invoice_id.move_type", "=", "invoice"),
            ("invoice_id.invoice_date", ">=", month_start), ("invoice_id.invoice_date", "<=", today),
        ])
        marge_month = sum(line.subtotal - line.qty * line.product_id.cost_price for line in lines_month)

        expense_env = self._readable_env("seyal.expense")["seyal.expense"]
        expenses_month = expense_env.search([
            ("state", "=", "confirmed"),
            ("expense_date", ">=", month_start), ("expense_date", "<=", today),
        ])
        depenses_month = sum(expenses_month.mapped("amount"))
        # Simplification honnete : marge brute - depenses du mois, pas une
        # comptabilite complete (pas de rapprochement bancaire, amortissements,
        # etc.) - RULE "ne pas inventer de donnee".
        benefice_month = marge_month - depenses_month

        product_env = self._readable_env("seyal.product")["seyal.product"]
        products = product_env.search([])
        stock_value = sum(p.qty_on_hand * p.cost_price for p in products)
        ruptures_count = len(products.filtered(
            lambda p: p.min_stock_qty > 0 and p.qty_on_hand <= p.min_stock_qty
        ))

        partner_env = self._readable_env("seyal.partner")["seyal.partner"]
        customers = partner_env.search([("is_customer", "=", True), ("balance", ">", 0)])
        creances_total = sum(customers.mapped("balance"))
        suppliers = partner_env.search([("is_supplier", "=", True), ("payable_balance", ">", 0)])
        dettes_total = sum(suppliers.mapped("payable_balance"))

        import_env = self._readable_env("seyal.import")["seyal.import"]
        importations_en_cours = import_env.search_count([("state", "!=", "receptionne")])

        delivery_env = self._readable_env("seyal.delivery")["seyal.delivery"]
        livraisons_en_cours = delivery_env.search_count([
            ("state", "not in", ("livree", "partielle", "probleme", "cloturee")),
        ])

        payment_env = self._readable_env("seyal.payment")["seyal.payment"]
        payments_month = payment_env.search([
            ("state", "=", "confirmed"),
            ("payment_date", ">=", month_start), ("payment_date", "<=", today),
        ])
        encaissements_month = sum(payments_month.mapped("amount"))

        return {
            "ca_today": ca_today,
            "ca_month": ca_month,
            "ventes_count": ventes_count,
            "ventes_amount": ventes_amount,
            "achats_amount": achats_amount,
            "marge_month": marge_month,
            "benefice_month": benefice_month,
            "stock_value": stock_value,
            "ruptures_count": ruptures_count,
            "creances_total": creances_total,
            "dettes_total": dettes_total,
            "importations_en_cours": importations_en_cours,
            "livraisons_en_cours": livraisons_en_cours,
            "depenses_month": depenses_month,
            "encaissements_month": encaissements_month,
        }

    @api.model
    def get_daily_series(self, days=30):
        today = fields.Date.context_today(self)
        invoice_env = self._readable_env("seyal.invoice")["seyal.invoice"]
        payment_env = self._readable_env("seyal.payment")["seyal.payment"]
        series = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            invoices = invoice_env.search([
                ("state", "=", "validated"), ("move_type", "=", "invoice"), ("invoice_date", "=", day),
            ])
            payments = payment_env.search([("state", "=", "confirmed"), ("payment_date", "=", day)])
            series.append({
                "date": fields.Date.to_string(day),
                "ca": sum(invoices.mapped("amount_total")),
                "encaisse": sum(payments.mapped("amount")),
            })
        return series
