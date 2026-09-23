from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalDriver(TransactionCase):
    def test_create_driver(self):
        driver = self.env["seyal.driver"].create({"name": "Chauffeur Test"})
        self.assertTrue(driver.active)

    @mute_logger("odoo.sql_db")
    def test_user_id_unique_per_driver(self):
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Chauffeur Utilisateur", "login": "driver_user_test", "email": "driver_test@example.com",
        })
        self.env["seyal.driver"].create({"name": "Chauffeur 1", "user_id": user.id})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.driver"].create({"name": "Chauffeur 2", "user_id": user.id})
