from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalLeave(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["seyal.employee"].create({"name": "Employe Conge"})

    def test_days_computed(self):
        leave = self.env["seyal.leave"].create({
            "employee_id": self.employee.id, "date_start": "2026-01-10", "date_end": "2026-01-14",
        })
        self.assertEqual(leave.days, 5)

    def test_end_before_start_invalid(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.leave"].create({
                "employee_id": self.employee.id, "date_start": "2026-01-14", "date_end": "2026-01-10",
            })

    def test_approve_workflow(self):
        leave = self.env["seyal.leave"].create({
            "employee_id": self.employee.id, "date_start": "2026-01-10", "date_end": "2026-01-10",
        })
        leave.action_approve()
        self.assertEqual(leave.state, "approved")

    def test_cannot_approve_twice(self):
        leave = self.env["seyal.leave"].create({
            "employee_id": self.employee.id, "date_start": "2026-01-10", "date_end": "2026-01-10",
        })
        leave.action_approve()
        with self.assertRaises(UserError):
            leave.action_approve()
