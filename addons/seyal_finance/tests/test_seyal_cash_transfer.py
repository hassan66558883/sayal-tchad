from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalCashTransfer(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cash_account = self.env["seyal.cash.account"].create({"name": "Caisse Transfert", "code": "CA-TRF"})
        self.bank_account = self.env["seyal.bank.account"].create({"name": "Banque Transfert"})

        # Give the cash account a real balance via a confirmed client payment.
        customer = self.env["seyal.partner"].create({"name": "Client Transfert", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids TRF"})
        kg = self.env["seyal.uom"].create({
            "name": "Kilogramme TRF", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        product = self.env["seyal.product"].create({"name": "Produit TRF", "uom_id": kg.id})
        invoice = self.env["seyal.invoice"].create({"customer_id": customer.id})
        self.env["seyal.invoice.line"].create({
            "invoice_id": invoice.id, "product_id": product.id, "qty": 10, "unit_price": 100.0,
        })
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({
            "invoice_id": invoice.id, "amount": 1000.0, "cash_account_id": self.cash_account.id,
        })
        payment.action_confirm()

    def test_cash_account_has_balance_from_payment(self):
        self.assertEqual(self.cash_account.balance, 1000.0)
        self.assertEqual(self.bank_account.balance, 0.0)

    def test_deposit_moves_money_from_cash_to_bank(self):
        transfer = self.env["seyal.cash.transfer"].create({
            "direction": "deposit", "cash_account_id": self.cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 600.0,
        })
        transfer.action_confirm()
        self.assertEqual(self.cash_account.balance, 400.0)
        self.assertEqual(self.bank_account.balance, 600.0)

    def test_deposit_blocked_if_insufficient_cash(self):
        transfer = self.env["seyal.cash.transfer"].create({
            "direction": "deposit", "cash_account_id": self.cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 5000.0,
        })
        with self.assertRaises(UserError):
            transfer.action_confirm()

    def test_withdrawal_moves_money_from_bank_to_cash(self):
        deposit = self.env["seyal.cash.transfer"].create({
            "direction": "deposit", "cash_account_id": self.cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 1000.0,
        })
        deposit.action_confirm()
        withdrawal = self.env["seyal.cash.transfer"].create({
            "direction": "withdrawal", "cash_account_id": self.cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 300.0,
        })
        withdrawal.action_confirm()
        self.assertEqual(self.cash_account.balance, 300.0)
        self.assertEqual(self.bank_account.balance, 700.0)

    def test_confirmed_transfer_is_immutable(self):
        transfer = self.env["seyal.cash.transfer"].create({
            "direction": "deposit", "cash_account_id": self.cash_account.id,
            "bank_account_id": self.bank_account.id, "amount": 100.0,
        })
        transfer.action_confirm()
        with self.assertRaises(UserError):
            transfer.write({"amount": 200.0})
