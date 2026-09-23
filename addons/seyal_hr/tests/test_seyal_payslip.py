from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalPayslip(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["seyal.employee"].create({"name": "Employe Paie", "salary": 150000.0})

    def test_create_payslip_generates_reference(self):
        payslip = self.env["seyal.payslip"].create({
            "employee_id": self.employee.id, "period_start": "2026-01-01", "period_end": "2026-01-31",
            "base_salary": 150000.0,
        })
        self.assertTrue(payslip.reference.startswith("PAI"))
        self.assertEqual(payslip.net_salary, 150000.0)

    def test_onchange_employee_sets_base_salary(self):
        payslip = self.env["seyal.payslip"].new({"employee_id": self.employee.id})
        payslip._onchange_employee_id()
        self.assertEqual(payslip.base_salary, 150000.0)

    def test_validate_deducts_approved_advances_in_period(self):
        advance_in = self.env["seyal.advance"].create({
            "employee_id": self.employee.id, "amount": 20000.0, "advance_date": "2026-01-15",
        })
        advance_in.action_approve()
        advance_out_of_period = self.env["seyal.advance"].create({
            "employee_id": self.employee.id, "amount": 5000.0, "advance_date": "2026-02-15",
        })
        advance_out_of_period.action_approve()
        advance_not_approved = self.env["seyal.advance"].create({
            "employee_id": self.employee.id, "amount": 3000.0, "advance_date": "2026-01-20",
        })

        payslip = self.env["seyal.payslip"].create({
            "employee_id": self.employee.id, "period_start": "2026-01-01", "period_end": "2026-01-31",
            "base_salary": 150000.0,
        })
        payslip.action_validate()

        self.assertEqual(payslip.advances_deducted, 20000.0)
        self.assertEqual(payslip.net_salary, 130000.0)
        self.assertEqual(advance_in.payslip_id, payslip)
        self.assertFalse(advance_out_of_period.payslip_id)
        self.assertFalse(advance_not_approved.payslip_id)

    def test_cannot_validate_twice(self):
        payslip = self.env["seyal.payslip"].create({
            "employee_id": self.employee.id, "period_start": "2026-01-01", "period_end": "2026-01-31",
            "base_salary": 150000.0,
        })
        payslip.action_validate()
        with self.assertRaises(UserError):
            payslip.action_validate()

    def test_mark_paid_requires_validated(self):
        payslip = self.env["seyal.payslip"].create({
            "employee_id": self.employee.id, "period_start": "2026-01-01", "period_end": "2026-01-31",
            "base_salary": 150000.0,
        })
        with self.assertRaises(UserError):
            payslip.action_mark_paid()
        payslip.action_validate()
        payslip.action_mark_paid()
        self.assertEqual(payslip.state, "paid")
