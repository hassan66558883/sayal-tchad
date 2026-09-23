from odoo.tests.common import TransactionCase


class TestSeyalEmployee(TransactionCase):
    def test_create_employee_generates_reference(self):
        employee = self.env["seyal.employee"].create({"name": "Employe Test", "salary": 150000.0})
        self.assertTrue(employee.reference.startswith("EMP"))
        self.assertIn("EMP", employee.display_name)
        self.assertIn("Employe Test", employee.display_name)
