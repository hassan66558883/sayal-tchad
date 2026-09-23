from odoo.tests.common import TransactionCase


class TestSeyalVehicleMaintenance(TransactionCase):
    def test_create_maintenance(self):
        vehicle = self.env["seyal.vehicle"].create({"name": "Camion Entretien", "plate_number": "TCH-ENT"})
        maintenance = self.env["seyal.vehicle.maintenance"].create({
            "vehicle_id": vehicle.id, "description": "Vidange", "cost": 25000.0, "odometer_km": 5000,
        })
        self.assertEqual(maintenance.cost, 25000.0)
