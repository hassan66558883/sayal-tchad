from odoo.tests.common import TransactionCase

from ..models.seyal_report_export_wizard import REPORT_TYPES


class TestSeyalReportExportWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Rapport", "is_customer": True})
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Rapport", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids rapport"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme rapport", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({
            "name": "Produit rapport", "uom_id": self.kg.id, "cost_price": 50.0,
        })

        order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id, "order_date": "2026-01-15"})
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        order.action_confirm()
        invoice_result = order.action_create_invoice()
        self.invoice = self.env["seyal.invoice"].browse(invoice_result["res_id"])
        self.invoice.invoice_date = "2026-01-16"
        self.invoice.action_validate()

    def _make_wizard(self, report_type):
        return self.env["seyal.report.export.wizard"].create({
            "report_type": report_type, "date_from": "2026-01-01", "date_to": "2026-01-31",
        })

    def test_all_report_types_return_without_error(self):
        for report_type, _label in REPORT_TYPES:
            wizard = self._make_wizard(report_type)
            title, columns, rows = wizard._compute_report_data()
            self.assertTrue(title)
            self.assertIsInstance(columns, list)
            self.assertIsInstance(rows, list)

    def test_ventes_report_includes_confirmed_order(self):
        wizard = self._make_wizard("ventes")
        _title, _columns, rows = wizard._compute_report_data()
        references = [row[0] for row in rows]
        # The order was auto-confirmed in setUp via action_confirm().
        orders = self.env["seyal.sale.order"].search([("customer_id", "=", self.customer.id)])
        self.assertIn(orders.reference, references)

    def test_marge_report_computes_real_margin(self):
        wizard = self._make_wizard("marge")
        _title, columns, rows = wizard._compute_report_data()
        self.assertEqual(len(rows), 1)
        # qty=10, unit_price=100 -> subtotal 1000 ; cost_price=50 -> cost=500 ; margin=500
        row = rows[0]
        ca_idx = columns.index("Chiffre d'affaires")
        cout_idx = columns.index("Cout")
        marge_idx = columns.index("Marge")
        self.assertEqual(row[ca_idx], 1000.0)
        self.assertEqual(row[cout_idx], 500.0)
        self.assertEqual(row[marge_idx], 500.0)

    def test_creances_report_includes_customer_with_balance(self):
        wizard = self._make_wizard("creances")
        _title, _columns, rows = wizard._compute_report_data()
        names = [row[1] for row in rows]
        self.assertIn(self.customer.name, names)

    def test_stock_report_lists_products(self):
        wizard = self._make_wizard("stock")
        _title, columns, rows = wizard._compute_report_data()
        names = [row[1] for row in rows]
        self.assertIn(self.product.name, names)

    def test_pdf_renders(self):
        wizard = self._make_wizard("ventes")
        # Odoo serves an HTML fallback instead of invoking wkhtmltopdf while
        # running under --test-enable - same environment-dependent behavior
        # already relied on by ste_billing's own report test in this repo.
        content, report_type = self.env["ir.actions.report"]._render_qweb_pdf(
            "seyal_reporting.report_seyal_generic_document", wizard.ids,
        )
        self.assertIn(report_type, ("pdf", "html"))
        self.assertTrue(content)

    def test_xlsx_export_creates_attachment(self):
        wizard = self._make_wizard("ventes")
        action = wizard.action_export_xlsx()
        self.assertEqual(action["type"], "ir.actions.act_url")
        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "seyal.report.export.wizard"), ("res_id", "=", wizard.id),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.datas)
        self.assertIn(str(attachment.id), action["url"])
