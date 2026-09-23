from odoo.tests.common import TransactionCase


class TestSeyalCashAccountBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cash_account = self.env["seyal.cash.account"].create({"name": "Caisse Solde", "code": "CA-SOL"})
        self.customer = self.env["seyal.partner"].create({"name": "Client Solde Caisse", "is_customer": True})
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Solde Caisse", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids solde caisse"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme solde caisse", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit solde caisse", "uom_id": self.kg.id})

    def test_balance_zero_initially(self):
        self.assertEqual(self.cash_account.balance, 0.0)

    def test_balance_increases_with_client_payment(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 5, "unit_price": 100.0,
        })
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 500.0, "cash_account_id": self.cash_account.id,
        })
        payment.action_confirm()
        self.assertEqual(self.cash_account.balance, 500.0)

    def test_balance_decreases_with_supplier_payment_and_expense(self):
        # Seed the cash account first.
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 10, "unit_price": 100.0,
        })
        invoice.action_validate()
        seed_payment = self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 1000.0, "cash_account_id": self.cash_account.id,
        })
        seed_payment.action_confirm()

        bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": bill.id, "product_id": self.product.id, "qty": 3, "unit_price": 100.0,
        })
        bill.action_validate()
        supplier_payment = self.env["seyal.supplier.payment"].create({
            "bill_id": bill.id, "amount": 300.0, "cash_account_id": self.cash_account.id,
        })
        supplier_payment.action_confirm()

        expense = self.env["seyal.expense"].create({
            "category": "carburant", "amount": 200.0, "cash_account_id": self.cash_account.id,
        })
        expense.action_confirm()

        self.assertEqual(self.cash_account.balance, 1000.0 - 300.0 - 200.0)

    def test_draft_payment_does_not_affect_balance(self):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": self.product.id, "qty": 5, "unit_price": 100.0,
        })
        invoice.action_validate()
        self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 500.0, "cash_account_id": self.cash_account.id,
        })
        self.assertEqual(self.cash_account.balance, 0.0)
