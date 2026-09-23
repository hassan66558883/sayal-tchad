from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalSupplierPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Paiement", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids PFR"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme PFR", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit PFR", "uom_id": self.kg.id})
        self.bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": self.bill.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        self.bill.action_validate()

    def test_create_payment_generates_reference(self):
        payment = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 500.0})
        self.assertTrue(payment.reference.startswith("PFR"))

    def test_cannot_pay_on_draft_bill(self):
        draft_bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": draft_bill.id, "product_id": self.product.id, "qty": 1, "unit_price": 10.0,
        })
        with self.assertRaises(ValidationError):
            self.env["seyal.supplier.payment"].create({"bill_id": draft_bill.id, "amount": 5.0})

    def test_cannot_overpay(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 2000.0})

    def test_partial_payments_update_bill_state(self):
        p1 = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 400.0})
        p1.action_confirm()
        self.assertEqual(self.bill.payment_state, "partially_paid")

        p2 = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 600.0})
        p2.action_confirm()
        self.assertEqual(self.bill.payment_state, "paid")
        self.assertEqual(self.bill.amount_due, 0.0)

    def test_second_payment_confirm_fails_if_cumulative_exceeds_due(self):
        p1 = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 700.0})
        p2 = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 700.0})
        p1.action_confirm()
        with self.assertRaises(ValidationError):
            p2.action_confirm()

    def test_confirmed_payment_is_immutable(self):
        payment = self.env["seyal.supplier.payment"].create({"bill_id": self.bill.id, "amount": 500.0})
        payment.action_confirm()
        with self.assertRaises(UserError):
            payment.write({"amount": 999.0})
