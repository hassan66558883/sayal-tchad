from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalStockLot(TransactionCase):
    def setUp(self):
        super().setUp()
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids lot"})
        kg = self.env["seyal.uom"].create({
            "name": "Kilogramme lot", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit lot", "uom_id": kg.id})

    def test_create_lot(self):
        lot = self.env["seyal.stock.lot"].create({"name": "LOT-0001", "product_id": self.product.id})
        self.assertTrue(lot.active)

    @mute_logger("odoo.sql_db")
    def test_lot_name_unique_per_product(self):
        self.env["seyal.stock.lot"].create({"name": "LOT-DUP", "product_id": self.product.id})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.stock.lot"].create({"name": "LOT-DUP", "product_id": self.product.id})
