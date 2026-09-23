from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalCommission(TransactionCase):
    def setUp(self):
        super().setUp()
        self.salesperson = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Commercial Commission", "login": "commercial_commission",
            "email": "commercial_commission@example.com",
        })
        self.customer = self.env["seyal.partner"].create({"name": "Client Commission", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids commission"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme commission", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit commission", "uom_id": self.kg.id})

        order = self.env["seyal.sale.order"].create({
            "customer_id": self.customer.id, "salesperson_id": self.salesperson.id, "order_date": "2026-01-10",
        })
        self.env["seyal.sale.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 10, "unit_price": 1000.0,
        })
        order.action_confirm()
        self.invoice_result = order.action_create_invoice()
        self.invoice = self.env["seyal.invoice"].browse(self.invoice_result["res_id"])
        self.invoice.action_validate()

    def _pay(self, amount, date):
        payment = self.env["seyal.payment"].create({
            "invoice_id": self.invoice.id, "amount": amount, "payment_date": date,
        })
        payment.action_confirm()
        return payment

    def test_create_commission_generates_reference(self):
        commission = self.env["seyal.commission"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "rate_percent": 5.0,
        })
        self.assertTrue(commission.reference.startswith("COM"))

    def test_compute_base_amount_from_confirmed_payments_in_period(self):
        self._pay(6000.0, "2026-01-15")
        commission = self.env["seyal.commission"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "rate_percent": 5.0,
        })
        commission.action_compute()
        self.assertEqual(commission.base_amount, 6000.0)
        self.assertEqual(commission.commission_amount, 300.0)

    def test_payment_outside_period_not_counted(self):
        self._pay(6000.0, "2026-02-15")
        commission = self.env["seyal.commission"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "rate_percent": 5.0,
        })
        commission.action_compute()
        self.assertEqual(commission.base_amount, 0.0)

    def test_onchange_salesperson_defaults_rate_from_rule(self):
        self.env["seyal.commission.rule"].create({
            "name": "Regle commercial commission", "salesperson_id": self.salesperson.id, "rate_percent": 8.0,
        })
        commission = self.env["seyal.commission"].new({})
        commission.salesperson_id = self.salesperson
        commission._onchange_salesperson_id()
        self.assertEqual(commission.rate_percent, 8.0)

    def test_cannot_validate_twice(self):
        commission = self.env["seyal.commission"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "rate_percent": 5.0,
        })
        commission.action_validate()
        with self.assertRaises(UserError):
            commission.action_validate()

    def test_cannot_recompute_validated_commission(self):
        commission = self.env["seyal.commission"].create({
            "salesperson_id": self.salesperson.id, "period_start": "2026-01-01",
            "period_end": "2026-01-31", "rate_percent": 5.0,
        })
        commission.action_validate()
        with self.assertRaises(UserError):
            commission.action_compute()
