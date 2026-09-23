from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalWarehouse(TransactionCase):
    def test_create_warehouse(self):
        warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Ndjamena", "code": "WH-NDJ"})
        self.assertTrue(warehouse.active)

    def test_default_company_is_seyal(self):
        warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Test", "code": "WH-T1"})
        self.assertEqual(warehouse.company_id, self.env.ref("seyal_base.seyal_company"))

    @mute_logger("odoo.sql_db")
    def test_code_must_be_unique(self):
        self.env["seyal.warehouse"].create({"name": "Entrepot A", "code": "WH-A"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.warehouse"].create({"name": "Entrepot B", "code": "WH-A"})
