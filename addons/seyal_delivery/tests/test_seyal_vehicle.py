from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalVehicle(TransactionCase):
    def test_create_vehicle(self):
        vehicle = self.env["seyal.vehicle"].create({"name": "Camion 10T", "plate_number": "TCH-001"})
        self.assertTrue(vehicle.active)

    @mute_logger("odoo.sql_db")
    def test_plate_number_unique(self):
        self.env["seyal.vehicle"].create({"name": "Camion A", "plate_number": "TCH-DUP"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.vehicle"].create({"name": "Camion B", "plate_number": "TCH-DUP"})
