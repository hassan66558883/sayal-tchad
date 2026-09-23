from odoo.tests.common import TransactionCase


class TestSeyalProductStock(TransactionCase):
    def setUp(self):
        super().setUp()
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids prod stock"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme prod stock", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit stock", "uom_id": self.kg.id})
        self.warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Prod", "code": "WH-PRD"})

    def test_qty_on_hand_reflects_done_moves(self):
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 40, "move_type": "in",
            "dest_warehouse_id": self.warehouse.id, "state": "done",
        })
        self.assertEqual(self.product.qty_on_hand, 40)

    def test_qty_in_transit_reflects_unreceived_import(self):
        supplier = self.env["seyal.partner"].create({"name": "Fournisseur Transit", "is_supplier": True})
        order = self.env["seyal.purchase.order"].create({"supplier_id": supplier.id, "is_import": True})
        self.env["seyal.purchase.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 25, "unit_price": 50.0,
        })
        order.action_confirm()
        self.env["seyal.import"].create({"purchase_order_id": order.id})
        self.assertEqual(self.product.qty_in_transit, 25)

    def test_qty_in_transit_zero_once_receptionne(self):
        supplier = self.env["seyal.partner"].create({"name": "Fournisseur Transit 2", "is_supplier": True})
        order = self.env["seyal.purchase.order"].create({"supplier_id": supplier.id, "is_import": True})
        self.env["seyal.purchase.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 25, "unit_price": 50.0,
        })
        order.action_confirm()
        imp = self.env["seyal.import"].create({"purchase_order_id": order.id})
        imp.action_expedier()
        imp.action_arrivee()
        imp.action_douane()
        imp.action_receptionner()
        self.assertEqual(self.product.qty_in_transit, 0)
