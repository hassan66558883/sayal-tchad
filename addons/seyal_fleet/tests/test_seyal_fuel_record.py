from odoo.tests.common import TransactionCase


class TestSeyalFuelRecord(TransactionCase):
    def setUp(self):
        super().setUp()
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Carburant", "plate_number": "TCH-CAR"})

    def test_create_fuel_record_generates_reference_and_amount(self):
        record = self.env["seyal.fuel.record"].create({
            "vehicle_id": self.vehicle.id, "odometer_km": 1000, "qty_liters": 50, "unit_price": 700.0,
        })
        self.assertTrue(record.reference.startswith("CAR"))
        self.assertEqual(record.amount, 35000.0)

    def test_qty_must_be_positive(self):
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.fuel.record"].create({
                    "vehicle_id": self.vehicle.id, "odometer_km": 1000, "qty_liters": -5, "unit_price": 700.0,
                })
