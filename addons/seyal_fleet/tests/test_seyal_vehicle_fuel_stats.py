from odoo.tests.common import TransactionCase


class TestSeyalVehicleFuelStats(TransactionCase):
    def setUp(self):
        super().setUp()
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Stats", "plate_number": "TCH-STA"})

    def test_no_stats_with_less_than_two_records(self):
        self.env["seyal.fuel.record"].create({
            "vehicle_id": self.vehicle.id, "odometer_km": 1000, "qty_liters": 50, "unit_price": 700.0,
        })
        self.assertEqual(self.vehicle.total_km, 0.0)
        self.assertEqual(self.vehicle.avg_consumption_l_per_100km, 0.0)
        self.assertEqual(self.vehicle.cost_per_km, 0.0)

    def test_consumption_and_cost_per_km_computed_from_records(self):
        self.env["seyal.fuel.record"].create({
            "vehicle_id": self.vehicle.id, "odometer_km": 1000, "qty_liters": 40, "unit_price": 700.0,
        })
        self.env["seyal.fuel.record"].create({
            "vehicle_id": self.vehicle.id, "odometer_km": 1500, "qty_liters": 60, "unit_price": 700.0,
        })
        # total_km = 1500 - 1000 = 500 ; total_liters = 100 ; total_cost = 70000
        self.assertEqual(self.vehicle.total_km, 500.0)
        self.assertEqual(self.vehicle.total_fuel_liters, 100.0)
        self.assertEqual(self.vehicle.total_fuel_cost, 70000.0)
        self.assertEqual(self.vehicle.avg_consumption_l_per_100km, 20.0)
        self.assertEqual(self.vehicle.cost_per_km, 140.0)
