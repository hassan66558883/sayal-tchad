from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({
            "name": "Client Test", "is_customer": True, "customer_type": "detaillant",
        })
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids SO"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme SO", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({
            "name": "Sucre SO", "uom_id": self.kg.id, "sale_price": 500.0,
            "wholesale_price": 400.0, "retail_price": 450.0,
        })

    def _make_order(self, with_line=True, qty=10, unit_price=450.0, discount=0.0):
        order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id})
        if with_line:
            self.env["seyal.sale.order.line"].create({
                "order_id": order.id, "product_id": self.product.id,
                "qty": qty, "unit_price": unit_price, "discount_percent": discount,
            })
        return order

    def test_create_order_generates_reference(self):
        order = self._make_order()
        self.assertTrue(order.reference.startswith("DEV"))

    def test_amount_total_with_discount(self):
        order = self._make_order(qty=10, unit_price=100.0, discount=10.0)
        self.assertEqual(order.amount_total, 900.0)

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

    def test_credit_limit_blocks_confirm(self):
        self.customer.credit_limit = 1000.0
        order = self._make_order(qty=10, unit_price=450.0)  # 4500 > 1000
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_credit_limit_allows_confirm_within_limit(self):
        self.customer.credit_limit = 10000.0
        order = self._make_order(qty=10, unit_price=450.0)  # 4500 <= 10000
        order.action_confirm()
        self.assertEqual(order.state, "confirmed")

    def test_no_credit_limit_set_never_blocks(self):
        order = self._make_order(qty=1000, unit_price=450.0)  # huge amount, but no limit set (0)
        order.action_confirm()
        self.assertEqual(order.state, "confirmed")

    def test_create_invoice_copies_lines(self):
        order = self._make_order(qty=10, unit_price=450.0)
        order.action_confirm()
        result = order.action_create_invoice()
        invoice = self.env["seyal.invoice"].browse(result["res_id"])
        self.assertEqual(invoice.sale_order_id, order)
        self.assertEqual(len(invoice.line_ids), 1)
        self.assertEqual(invoice.amount_total, 4500.0)
        self.assertEqual(invoice.state, "draft")

    def test_cannot_invoice_draft_order(self):
        order = self._make_order()
        with self.assertRaises(UserError):
            order.action_create_invoice()

    def test_onchange_customer_sets_branch_and_salesperson(self):
        branch = self.env["seyal.branch"].create({"name": "Agence SO", "code": "ASO"})
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Commercial SO", "login": "commercial_so", "email": "commercial_so@example.com",
        })
        self.customer.write({"branch_id": branch.id, "salesperson_id": user.id})
        order = self.env["seyal.sale.order"].new({"customer_id": self.customer.id})
        order._onchange_customer_id()
        self.assertEqual(order.branch_id, branch)
        self.assertEqual(order.salesperson_id, user)
