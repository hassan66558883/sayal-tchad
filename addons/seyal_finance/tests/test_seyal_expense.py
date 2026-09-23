from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalExpense(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cash_account = self.env["seyal.cash.account"].create({"name": "Caisse Depense", "code": "CA-DEP"})

    def test_create_expense_generates_reference(self):
        expense = self.env["seyal.expense"].create({"category": "loyer", "amount": 50000.0})
        self.assertTrue(expense.reference.startswith("DEP"))

    def test_cannot_set_both_cash_and_bank(self):
        bank = self.env["seyal.bank.account"].create({"name": "Banque Depense"})
        with self.assertRaises(ValidationError):
            self.env["seyal.expense"].create({
                "category": "electricite", "amount": 10000.0,
                "cash_account_id": self.cash_account.id, "bank_account_id": bank.id,
            })

    def test_confirm_workflow(self):
        expense = self.env["seyal.expense"].create({
            "category": "carburant", "amount": 15000.0, "cash_account_id": self.cash_account.id,
        })
        expense.action_confirm()
        self.assertEqual(expense.state, "confirmed")

    def test_confirmed_expense_is_immutable(self):
        expense = self.env["seyal.expense"].create({"category": "autre", "amount": 1000.0})
        expense.action_confirm()
        with self.assertRaises(UserError):
            expense.write({"amount": 2000.0})

    def test_cannot_cancel_confirmed_expense(self):
        expense = self.env["seyal.expense"].create({"category": "autre", "amount": 1000.0})
        expense.action_confirm()
        with self.assertRaises(UserError):
            expense.action_cancel()
