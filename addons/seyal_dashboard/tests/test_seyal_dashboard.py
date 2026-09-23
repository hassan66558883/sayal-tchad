from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestSeyalDashboard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Dashboard", "is_customer": True})
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Dashboard", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids dashboard"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme dashboard", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({
            "name": "Produit dashboard", "uom_id": self.kg.id, "cost_price": 40.0, "min_stock_qty": 100,
        })
        self.warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Dashboard", "code": "WH-DASH"})

        self.today = fields.Date.context_today(self.env.user)

        order = self.env["seyal.sale.order"].create({
            "customer_id": self.customer.id, "order_date": self.today,
        })
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        order.action_confirm()
        invoice_result = order.action_create_invoice()
        self.invoice = self.env["seyal.invoice"].browse(invoice_result["res_id"])
        self.invoice.invoice_date = self.today
        self.invoice.action_validate()
        payment = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 400.0})
        payment.payment_date = self.today
        payment.action_confirm()

        purchase_order = self.env["seyal.purchase.order"].create({
            "supplier_id": self.supplier.id, "order_date": self.today,
        })
        self.env["seyal.purchase.order.line"].create({
            "order_id": purchase_order.id, "product_id": self.product.id, "qty": 5, "unit_price": 30.0,
        })
        purchase_order.action_confirm()

        expense = self.env["seyal.expense"].create({
            "category": "autre", "amount": 50.0, "expense_date": self.today,
        })
        expense.action_confirm()

    def test_get_kpis_ventes_and_achats(self):
        kpis = self.env["seyal.dashboard"].get_kpis()
        self.assertEqual(kpis["ventes_count"], 1)
        self.assertEqual(kpis["ventes_amount"], 1000.0)
        self.assertEqual(kpis["achats_amount"], 150.0)

    def test_get_kpis_ca_and_marge(self):
        kpis = self.env["seyal.dashboard"].get_kpis()
        self.assertEqual(kpis["ca_today"], 1000.0)
        self.assertEqual(kpis["ca_month"], 1000.0)
        # subtotal 1000 - (10 * cost_price 40) = 600
        self.assertEqual(kpis["marge_month"], 600.0)
        self.assertEqual(kpis["depenses_month"], 50.0)
        self.assertEqual(kpis["benefice_month"], 550.0)

    def test_get_kpis_encaissements(self):
        kpis = self.env["seyal.dashboard"].get_kpis()
        self.assertEqual(kpis["encaissements_month"], 400.0)

    def test_get_kpis_creances(self):
        kpis = self.env["seyal.dashboard"].get_kpis()
        # invoice total 1000, paid 400 -> balance 600
        self.assertEqual(kpis["creances_total"], 600.0)

    def test_get_kpis_ruptures(self):
        kpis = self.env["seyal.dashboard"].get_kpis()
        # qty_on_hand 0 (no stock move), min_stock_qty 100 -> in rupture
        self.assertEqual(kpis["ruptures_count"], 1)

    def test_get_kpis_no_rupture_once_stocked(self):
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 200, "move_type": "in",
            "dest_warehouse_id": self.warehouse.id, "state": "done",
        })
        kpis = self.env["seyal.dashboard"].get_kpis()
        self.assertEqual(kpis["ruptures_count"], 0)
        self.assertEqual(kpis["stock_value"], 200 * 40.0)

    def test_get_daily_series_length_and_today_value(self):
        series = self.env["seyal.dashboard"].get_daily_series(days=7)
        self.assertEqual(len(series), 7)
        today_entry = series[-1]
        self.assertEqual(today_entry["date"], str(self.today))
        self.assertEqual(today_entry["ca"], 1000.0)
        self.assertEqual(today_entry["encaisse"], 400.0)

    def test_call_kw_dispatch_survives_rpc_style_call(self):
        # Regression guard for the exact bug ste_dashboard documents in this
        # repo : overriding an RPC-called method without @api.model makes
        # Odoo's dispatcher (odoo.api.call_kw) expect a leading ids list,
        # raising IndexError for every caller. A direct Python call (as in
        # the tests above) never exercises that dispatch path at all.
        from odoo.api import call_kw

        Dashboard = self.env["seyal.dashboard"]
        call_kw(Dashboard, "get_kpis", [], {})
        call_kw(Dashboard, "get_daily_series", [], {"days": 7})

    def test_dashboard_accessible_to_role_without_direct_model_access(self):
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Chauffeur Dashboard", "login": "chauffeur_dashboard",
            "email": "chauffeur_dashboard@example.com",
            "groups_id": [(6, 0, [self.env.ref("seyal_security.group_seyal_chauffeur").id])],
        })
        with self.assertRaises(AccessError):
            self.env["seyal.invoice"].with_user(user).search([])
        try:
            self.env["seyal.dashboard"].with_user(user).get_kpis()
        except AccessError:
            self.fail("get_kpis() should not raise AccessError for a role without direct model access")
