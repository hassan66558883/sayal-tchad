from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Paiement", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids PAY"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme PAY", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit paiement", "uom_id": self.kg.id})
        self.invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": self.invoice.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        self.invoice.action_validate()

    def test_create_payment_generates_reference(self):
        payment = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 500.0})
        self.assertTrue(payment.reference.startswith("PAY"))

    def test_cannot_pay_on_draft_invoice(self):
        draft_invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": draft_invoice.id, "product_id": self.product.id, "qty": 1, "unit_price": 10.0,
        })
        with self.assertRaises(ValidationError):
            self.env["seyal.payment"].create({"invoice_id": draft_invoice.id, "amount": 5.0})

    def test_cannot_overpay(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 2000.0})

    def test_partial_payments_update_invoice_state(self):
        p1 = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 400.0})
        p1.action_confirm()
        self.assertEqual(self.invoice.payment_state, "partially_paid")
        self.assertEqual(self.invoice.amount_due, 600.0)

        p2 = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 600.0})
        p2.action_confirm()
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertEqual(self.invoice.amount_due, 0.0)

    def test_second_payment_confirm_fails_if_cumulative_exceeds_due(self):
        p1 = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 700.0})
        p2 = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 700.0})
        p1.action_confirm()
        with self.assertRaises(ValidationError):
            p2.action_confirm()

    def test_draft_payment_does_not_count_as_paid(self):
        self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 500.0})
        self.assertEqual(self.invoice.payment_state, "not_paid")
        self.assertEqual(self.invoice.amount_due, 1000.0)

    def test_confirmed_payment_is_immutable(self):
        payment = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 500.0})
        payment.action_confirm()
        with self.assertRaises(UserError):
            payment.write({"amount": 999.0})

    def test_cannot_cancel_confirmed_payment(self):
        payment = self.env["seyal.payment"].create({"invoice_id": self.invoice.id, "amount": 500.0})
        payment.action_confirm()
        with self.assertRaises(UserError):
            payment.action_cancel()
