from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalBranch(TransactionCase):
    def test_create_branch(self):
        branch = self.env["seyal.branch"].create({
            "name": "Agence N'Djamena Centre",
            "code": "NDJ-C",
        })
        self.assertEqual(branch.name, "Agence N'Djamena Centre")
        self.assertTrue(branch.active)

    @mute_logger("odoo.sql_db")
    def test_code_must_be_unique(self):
        self.env["seyal.branch"].create({"name": "Agence A", "code": "A-1"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.branch"].create({"name": "Agence B", "code": "A-1"})

    def test_display_name_shows_code(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Moundou", "code": "MDU"})
        self.assertIn("MDU", branch.display_name)
        self.assertIn("Agence Moundou", branch.display_name)

    def test_default_company_is_seyal(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Sarh", "code": "SRH"})
        self.assertEqual(branch.company_id, self.env.ref("seyal_base.seyal_company"))
