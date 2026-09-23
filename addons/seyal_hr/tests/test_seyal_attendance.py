from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalAttendance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env["seyal.employee"].create({"name": "Employe Presence"})

    def test_hours_worked_computed(self):
        attendance = self.env["seyal.attendance"].create({
            "employee_id": self.employee.id,
            "check_in": "2026-01-10 08:00:00", "check_out": "2026-01-10 17:00:00",
        })
        self.assertEqual(attendance.hours_worked, 9.0)

    def test_no_checkout_yet(self):
        attendance = self.env["seyal.attendance"].create({
            "employee_id": self.employee.id, "check_in": "2026-01-10 08:00:00",
        })
        self.assertEqual(attendance.hours_worked, 0.0)

    def test_checkout_before_checkin_invalid(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.attendance"].create({
                "employee_id": self.employee.id,
                "check_in": "2026-01-10 17:00:00", "check_out": "2026-01-10 08:00:00",
            })
