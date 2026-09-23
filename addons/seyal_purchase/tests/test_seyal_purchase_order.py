from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalPurchaseOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Test", "is_supplier": True})
        self.uom_categ = self.env["seyal.uom.category"].create({"name": "Poids PO"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme PO", "category_id": self.uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Riz", "uom_id": self.kg.id})

    def _make_order(self, with_line=True):
        order = self.env["seyal.purchase.order"].create({"supplier_id": self.supplier.id})
        if with_line:
            self.env["seyal.purchase.order.line"].create({
                "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
            })
        return order

    def test_create_order_generates_reference(self):
        order = self._make_order()
        self.assertTrue(order.reference.startswith("BC"))

    def test_amount_total_computed_from_lines(self):
        order = self._make_order()
        self.assertEqual(order.amount_total, 1000.0)

    def test_cannot_confirm_without_lines(self):
        order = self._make_order(with_line=False)
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_confirm_then_done_workflow(self):
        order = self._make_order()
        order.action_confirm()
        self.assertEqual(order.state, "confirmed")
        order.action_done()
        self.assertEqual(order.state, "done")

    def test_cannot_confirm_twice(self):
        order = self._make_order()
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_cannot_cancel_done_order(self):
        order = self._make_order()
        order.action_confirm()
        order.action_done()
        with self.assertRaises(UserError):
            order.action_cancel()

    def test_cancel_and_reset_to_draft(self):
        order = self._make_order()
        order.action_cancel()
        self.assertEqual(order.state, "cancelled")
        order.action_reset_to_draft()
        self.assertEqual(order.state, "draft")

    def test_default_company_is_seyal(self):
        order = self._make_order()
        self.assertEqual(order.company_id, self.env.ref("seyal_base.seyal_company"))

    def test_create_writes_audit_log(self):
        order = self._make_order()
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.purchase.order"), ("res_id", "=", order.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)

    def test_line_qty_must_be_positive(self):
        order = self._make_order(with_line=False)
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.purchase.order.line"].create({
                    "order_id": order.id, "product_id": self.product.id, "qty": -1, "unit_price": 100.0,
                })
