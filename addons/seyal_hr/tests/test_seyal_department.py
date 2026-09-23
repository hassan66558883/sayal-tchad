from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalDepartment(TransactionCase):
    def test_create_department(self):
        department = self.env["seyal.department"].create({"name": "Ventes", "code": "DPT-VTE"})
        self.assertTrue(department.active)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self.env["seyal.department"].create({"name": "Achats", "code": "DPT-ACH"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.department"].create({"name": "Autre", "code": "DPT-ACH"})
