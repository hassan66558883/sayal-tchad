from odoo.tests.common import TransactionCase


class TestSeyalBankAccountBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.bank_account = self.env["seyal.bank.account"].create({"name": "Banque Solde"})
        self.customer = self.env["seyal.partner"].create({"name": "Client Solde Banque", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids solde banque"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme solde banque", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit solde banque", "uom_id": self.kg.id})

    def test_balance_increases_with_client_payment(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 8, "unit_price": 100.0,
        })
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 800.0, "bank_account_id": self.bank_account.id,
        })
        payment.action_confirm()
        self.assertEqual(self.bank_account.balance, 800.0)

    def test_deposit_increases_bank_balance(self):
        cash_account = self.env["seyal.cash.account"].create({"name": "Caisse pour banque", "code": "CA-B1"})
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 1000.0, "cash_account_id": cash_account.id,
        })
        payment.action_confirm()
        transfer = self.env["seyal.cash.transfer"].create({
            "direction": "deposit", "cash_account_id": cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 700.0,
        })
        transfer.action_confirm()
        self.assertEqual(self.bank_account.balance, 700.0)
        self.assertEqual(cash_account.balance, 300.0)
