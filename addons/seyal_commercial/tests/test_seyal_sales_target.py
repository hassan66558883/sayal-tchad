from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalSalesTarget(TransactionCase):
    def setUp(self):
        super().setUp()
        self.salesperson = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Commercial Objectif", "login": "commercial_objectif", "email": "commercial_obj@example.com",
        })
        self.customer = self.env["seyal.partner"].create({"name": "Client Objectif", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids objectif"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme objectif", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit objectif", "uom_id": self.kg.id})

    def test_create_target_generates_reference(self):
        target = self.env["seyal.sales.target"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "target_amount": 100000.0,
        })
        self.assertTrue(target.reference.startswith("OBJ"))

    def test_end_date_must_be_after_start(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.sales.target"].create({
                "salesperson_id": self.salesperson.id, "period_start": "2026-02-01",
                "period_end": "2026-01-01", "target_amount": 100000.0,
            })

    def test_compute_achieved_amount_from_confirmed_orders(self):
        order = self.env["seyal.sale.order"].create({
            "customer_id": self.customer.id, "salesperson_id": self.salesperson.id, "order_date": "2026-01-15",
        })
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 1000.0,
        })
        order.action_confirm()

        target = self.env["seyal.sales.target"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "target_amount": 20000.0,
        })
        target.action_compute()
        self.assertEqual(target.achieved_amount, 10000.0)
        self.assertEqual(target.achievement_rate, 50.0)

    def test_draft_order_not_counted(self):
        order = self.env["seyal.sale.order"].create({
            "customer_id": self.customer.id, "salesperson_id": self.salesperson.id, "order_date": "2026-01-15",
        })
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 1000.0,
        })
        target = self.env["seyal.sales.target"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "target_amount": 20000.0,
        })
        target.action_compute()
        self.assertEqual(target.achieved_amount, 0.0)

    def test_order_outside_period_not_counted(self):
        order = self.env["seyal.sale.order"].create({
            "customer_id": self.customer.id, "salesperson_id": self.salesperson.id, "order_date": "2026-03-01",
        })
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 1000.0,
        })
        order.action_confirm()
        target = self.env["seyal.sales.target"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "target_amount": 20000.0,
        })
        target.action_compute()
        self.assertEqual(target.achieved_amount, 0.0)
