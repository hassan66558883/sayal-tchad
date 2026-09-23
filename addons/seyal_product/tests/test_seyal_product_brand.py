from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalProductBrand(TransactionCase):
    def test_create_brand(self):
        brand = self.env["seyal.product.brand"].create({"name": "Marque Test", "code": "MTS"})
        self.assertTrue(brand.active)

    @mute_logger("odoo.sql_db")
    def test_code_must_be_unique(self):
        self.env["seyal.product.brand"].create({"name": "Marque A", "code": "MA"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.product.brand"].create({"name": "Marque B", "code": "MA"})
