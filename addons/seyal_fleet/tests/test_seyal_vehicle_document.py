from odoo.tests.common import TransactionCase


class TestSeyalVehicleDocument(TransactionCase):
    def test_create_document(self):
        vehicle = self.env["seyal.vehicle"].create({"name": "Camion Document", "plate_number": "TCH-DOC"})
        document = self.env["seyal.vehicle.document"].create({
            "vehicle_id": vehicle.id, "name": "Carte grise", "document_type": "carte_grise",
        })
        self.assertEqual(document.document_type, "carte_grise")
