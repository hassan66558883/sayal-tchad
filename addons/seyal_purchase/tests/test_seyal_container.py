from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalContainer(TransactionCase):
    def setUp(self):
        super().setUp()
        supplier = self.env["seyal.partner"].create({"name": "Fournisseur Conteneur", "is_supplier": True})
        order = self.env["seyal.purchase.order"].create({"supplier_id": supplier.id, "is_import": True})
        self.import_rec = self.env["seyal.import"].create({"purchase_order_id": order.id})

    def test_create_container(self):
        container = self.env["seyal.container"].create({
            "number": "MSCU1234567", "import_id": self.import_rec.id,
        })
        self.assertEqual(container.status, "in_transit")

    @mute_logger("odoo.sql_db")
    def test_number_must_be_unique(self):
        self.env["seyal.container"].create({"number": "DUPL0000001", "import_id": self.import_rec.id})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.container"].create({"number": "DUPL0000001", "import_id": self.import_rec.id})

    def test_container_linked_via_one2many(self):
        self.env["seyal.container"].create({"number": "ONE20000001", "import_id": self.import_rec.id})
        self.assertEqual(len(self.import_rec.container_ids), 1)
