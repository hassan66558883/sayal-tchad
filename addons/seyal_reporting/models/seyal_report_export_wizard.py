import base64
import io

from odoo import fields, models
from odoo.exceptions import UserError

REPORT_TYPES = [
    ("ventes", "Ventes"),
    ("achats", "Achats"),
    ("stock", "Stock"),
    ("importations", "Importations"),
    ("clients", "Clients"),
    ("fournisseurs", "Fournisseurs"),
    ("creances", "Creances"),
    ("dettes", "Dettes fournisseurs"),
    ("marge", "Marge / Benefice"),
    ("commerciaux", "Commerciaux (commissions)"),
    ("livraisons", "Livraisons"),
    ("vehicules", "Vehicules"),
    ("carburant", "Carburant"),
    ("depenses", "Depenses"),
    ("caisse", "Caisse"),
    ("banque", "Banque"),
]


class SeyalReportExportWizard(models.TransientModel):
    _name = "seyal.report.export.wizard"
    _description = "Assistant d'export de rapport SEYAL-TCHAD"

    report_type = fields.Selection(REPORT_TYPES, string="Type de rapport", required=True, default="ventes")
    date_from = fields.Date(string="Du", required=True, default=lambda self: fields.Date.context_today(self))
    date_to = fields.Date(string="Au", required=True, default=lambda self: fields.Date.context_today(self))

    def _compute_report_data(self):
        self.ensure_one()
        method = getattr(self, "_data_%s" % self.report_type, None)
        if not method:
            raise UserError("Type de rapport inconnu : %s" % self.report_type)
        return method()

    def get_report_title(self):
        title, _columns, _rows = self._compute_report_data()
        return title

    def get_report_columns(self):
        _title, columns, _rows = self._compute_report_data()
        return columns

    def get_report_rows(self):
        _title, _columns, rows = self._compute_report_data()
        return rows

    # -----------------------------------------------------------------
    # Sources de donnees - une methode par type de rapport du cahier des
    # charges, chacune interrogeant les vrais modeles construits dans les
    # phases precedentes.
    # -----------------------------------------------------------------

    def _data_ventes(self):
        orders = self.env["seyal.sale.order"].search([
            ("order_date", ">=", self.date_from), ("order_date", "<=", self.date_to),
            ("state", "in", ("confirmed", "done")),
        ])
        columns = ["Reference", "Client", "Date", "Statut", "Montant"]
        rows = [
            [o.reference, o.customer_id.name, str(o.order_date), o.state, o.amount_total]
            for o in orders
        ]
        return "Ventes", columns, rows

    def _data_achats(self):
        orders = self.env["seyal.purchase.order"].search([
            ("order_date", ">=", self.date_from), ("order_date", "<=", self.date_to),
            ("state", "in", ("confirmed", "done")),
        ])
        columns = ["Reference", "Fournisseur", "Date", "Statut", "Montant"]
        rows = [
            [o.reference, o.supplier_id.name, str(o.order_date), o.state, o.amount_total]
            for o in orders
        ]
        return "Achats", columns, rows

    def _data_stock(self):
        products = self.env["seyal.product"].search([])
        columns = ["Reference", "Produit", "Stock disponible", "Stock minimum", "Stock en transit"]
        rows = [
            [p.reference, p.name, p.qty_on_hand, p.min_stock_qty, p.qty_in_transit]
            for p in products
        ]
        return "Stock", columns, rows

    def _data_importations(self):
        imports = self.env["seyal.import"].search([
            ("arrival_date", ">=", self.date_from), ("arrival_date", "<=", self.date_to),
        ])
        columns = ["Reference", "Fournisseur", "Statut", "Date d'arrivee", "Cout reel"]
        rows = [
            [i.reference, i.supplier_id.name, i.state, str(i.arrival_date or ""), i.real_cost]
            for i in imports
        ]
        return "Importations", columns, rows

    def _data_clients(self):
        customers = self.env["seyal.partner"].search([("is_customer", "=", True)])
        columns = ["Reference", "Nom", "Type", "Telephone", "Solde"]
        rows = [
            [c.reference, c.name, c.customer_type or "", c.phone or "", c.balance]
            for c in customers
        ]
        return "Clients", columns, rows

    def _data_fournisseurs(self):
        suppliers = self.env["seyal.partner"].search([("is_supplier", "=", True)])
        columns = ["Reference", "Nom", "Telephone", "Solde du (dette)"]
        rows = [
            [s.reference, s.name, s.phone or "", s.payable_balance]
            for s in suppliers
        ]
        return "Fournisseurs", columns, rows

    def _data_creances(self):
        customers = self.env["seyal.partner"].search([("is_customer", "=", True), ("balance", ">", 0)])
        columns = ["Reference", "Client", "Limite de credit", "Solde (creance)"]
        rows = [
            [c.reference, c.name, c.credit_limit, c.balance]
            for c in customers
        ]
        return "Creances clients", columns, rows

    def _data_dettes(self):
        suppliers = self.env["seyal.partner"].search([("is_supplier", "=", True), ("payable_balance", ">", 0)])
        columns = ["Reference", "Fournisseur", "Solde du (dette)"]
        rows = [
            [s.reference, s.name, s.payable_balance]
            for s in suppliers
        ]
        return "Dettes fournisseurs", columns, rows

    def _data_marge(self):
        lines = self.env["seyal.invoice.line"].search([
            ("invoice_id.state", "=", "validated"),
            ("invoice_id.move_type", "=", "invoice"),
            ("invoice_id.invoice_date", ">=", self.date_from),
            ("invoice_id.invoice_date", "<=", self.date_to),
        ])
        columns = ["Facture", "Produit", "Quantite", "Chiffre d'affaires", "Cout", "Marge"]
        rows = []
        for line in lines:
            cost = line.qty * line.product_id.cost_price
            margin = line.subtotal - cost
            rows.append([line.invoice_id.reference, line.product_id.name, line.qty, line.subtotal, cost, margin])
        return "Marge / Benefice", columns, rows

    def _data_commerciaux(self):
        commissions = self.env["seyal.commission"].search([
            ("period_start", "<=", self.date_to), ("period_end", ">=", self.date_from),
            ("state", "=", "validated"),
        ])
        columns = ["Commercial", "Periode", "Base", "Taux (%)", "Commission"]
        rows = [
            [
                c.salesperson_id.name, "%s - %s" % (c.period_start, c.period_end),
                c.base_amount, c.rate_percent, c.commission_amount,
            ]
            for c in commissions
        ]
        return "Commerciaux (commissions)", columns, rows

    def _data_livraisons(self):
        domain = [("state", "!=", "planifiee")]
        deliveries = self.env["seyal.delivery"].search(domain)
        columns = ["Reference", "Client", "Statut", "Date de livraison"]
        rows = [
            [d.reference, d.customer_id.name, d.state, str(d.delivery_datetime or "")]
            for d in deliveries
        ]
        return "Livraisons", columns, rows

    def _data_vehicules(self):
        vehicles = self.env["seyal.vehicle"].search([])
        columns = ["Vehicule", "Immatriculation", "Kilometrage parcouru", "Conso (L/100km)", "Cout/km"]
        rows = [
            [v.name, v.plate_number, v.total_km, v.avg_consumption_l_per_100km, v.cost_per_km]
            for v in vehicles
        ]
        return "Vehicules", columns, rows

    def _data_carburant(self):
        records = self.env["seyal.fuel.record"].search([
            ("record_date", ">=", self.date_from), ("record_date", "<=", self.date_to),
        ])
        columns = ["Vehicule", "Date", "Kilometrage", "Litres", "Montant"]
        rows = [
            [r.vehicle_id.name, str(r.record_date), r.odometer_km, r.qty_liters, r.amount]
            for r in records
        ]
        return "Carburant", columns, rows

    def _data_depenses(self):
        expenses = self.env["seyal.expense"].search([
            ("expense_date", ">=", self.date_from), ("expense_date", "<=", self.date_to),
            ("state", "=", "confirmed"),
        ])
        columns = ["Reference", "Categorie", "Date", "Montant"]
        rows = [
            [e.reference, e.category, str(e.expense_date), e.amount]
            for e in expenses
        ]
        return "Depenses", columns, rows

    def _data_caisse(self):
        accounts = self.env["seyal.cash.account"].search([])
        columns = ["Caisse", "Agence", "Solde"]
        rows = [
            [a.name, a.branch_id.name or "", a.balance]
            for a in accounts
        ]
        return "Caisse", columns, rows

    def _data_banque(self):
        accounts = self.env["seyal.bank.account"].search([])
        columns = ["Compte", "Banque", "Solde"]
        rows = [
            [a.name, a.bank_name or "", a.balance]
            for a in accounts
        ]
        return "Banque", columns, rows

    # -----------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------

    def action_export_pdf(self):
        self.ensure_one()
        return self.env.ref("seyal_reporting.action_report_seyal_generic").report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        import xlsxwriter

        title, columns, rows = self._compute_report_data()
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        sheet = workbook.add_worksheet("Rapport")
        bold = workbook.add_format({"bold": True})
        sheet.write(0, 0, title, bold)
        sheet.write(1, 0, "Periode : %s - %s" % (self.date_from, self.date_to))
        for col_idx, col_name in enumerate(columns):
            sheet.write(3, col_idx, col_name, bold)
        for row_idx, row in enumerate(rows, start=4):
            sheet.write_row(row_idx, 0, [c if c is not None else "" for c in row])
        workbook.close()
        content = buffer.getvalue()

        attachment = self.env["ir.attachment"].create({
            "name": "rapport_%s.xlsx" % self.report_type,
            "type": "binary",
            "datas": base64.b64encode(content),
            "res_model": self._name,
            "res_id": self.id,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }
