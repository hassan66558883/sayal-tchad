from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalVehicleInsurance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Assurance", "plate_number": "TCH-ASS"})

    def test_create_insurance(self):
        insurance = self.env["seyal.vehicle.insurance"].create({
            "vehicle_id": self.vehicle.id, "policy_number": "POL-001",
            "start_date": "2026-01-01", "end_date": "2026-12-31", "cost": 150000.0,
        })
        self.assertEqual(insurance.policy_number, "POL-001")

    def test_end_date_must_be_after_start_date(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.vehicle.insurance"].create({
                "vehicle_id": self.vehicle.id, "policy_number": "POL-002",
                "start_date": "2026-06-01", "end_date": "2026-01-01",
            })
