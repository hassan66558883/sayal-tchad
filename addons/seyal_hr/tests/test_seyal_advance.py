from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalAdvance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["seyal.employee"].create({"name": "Employe Avance", "salary": 100000.0})

    def test_create_advance_generates_reference(self):
        advance = self.env["seyal.advance"].create({"employee_id": self.employee.id, "amount": 20000.0})
        self.assertTrue(advance.reference.startswith("AVC"))

    def test_approve_workflow(self):
        advance = self.env["seyal.advance"].create({"employee_id": self.employee.id, "amount": 20000.0})
        advance.action_approve()
        self.assertEqual(advance.state, "approved")

    def test_cannot_cancel_advance_linked_to_payslip(self):
        advance = self.env["seyal.advance"].create({
            "employee_id": self.employee.id, "amount": 20000.0, "advance_date": "2026-01-10",
        })
        advance.action_approve()
        payslip = self.env["seyal.payslip"].create({
            "employee_id": self.employee.id, "period_start": "2026-01-01", "period_end": "2026-01-31",
            "base_salary": 100000.0,
        })
        payslip.action_validate()
        with self.assertRaises(UserError):
            advance.action_cancel()
