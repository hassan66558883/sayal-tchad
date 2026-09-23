from odoo.tests.common import TransactionCase


class TestSeyalPartnerBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Solde", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids solde"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme solde", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit solde", "uom_id": self.kg.id})

    def test_balance_zero_with_no_invoice(self):
        self.assertEqual(self.customer.balance, 0.0)

    def test_balance_reflects_unpaid_invoice(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        invoice.action_validate()
        self.assertEqual(self.customer.balance, 1000.0)

    def test_balance_decreases_after_payment(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({"invoice_id": invoice.id, "amount": 400.0})
        payment.action_confirm()
        self.assertEqual(self.customer.balance, 600.0)

    def test_draft_invoice_does_not_affect_balance(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        self.assertEqual(self.customer.balance, 0.0)
