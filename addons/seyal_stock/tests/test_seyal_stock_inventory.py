from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalStockInventory(TransactionCase):
    def setUp(self):
        super().setUp()
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids inv"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme inv", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit inventaire", "uom_id": self.kg.id})
        self.warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Inv", "code": "WH-INV"})
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 50, "move_type": "in",
            "dest_warehouse_id": self.warehouse.id, "state": "done",
        })

    def test_system_qty_matches_stock_moves(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        line = self.env["seyal.stock.inventory.line"].create({
            "inventory_id": inventory.id, "product_id": self.product.id, "counted_qty": 50,
        })
        self.assertEqual(line.system_qty, 50)
        self.assertEqual(line.difference, 0)

    def test_validate_with_positive_difference_creates_adjustment_in(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        self.env["seyal.stock.inventory.line"].create({
            "inventory_id": inventory.id, "product_id": self.product.id, "counted_qty": 60,
        })
        inventory.action_validate()
        self.assertEqual(inventory.state, "done")
        adjustment = self.env["seyal.stock.move"].search([
            ("product_id", "=", self.product.id), ("move_type", "=", "adjustment_in"),
        ])
        self.assertEqual(len(adjustment), 1)
        self.assertEqual(adjustment.qty, 10)
        self.assertEqual(adjustment.state, "done")
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.warehouse.id), 60,
        )

    def test_validate_with_negative_difference_creates_adjustment_out(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        self.env["seyal.stock.inventory.line"].create({
            "inventory_id": inventory.id, "product_id": self.product.id, "counted_qty": 35,
        })
        inventory.action_validate()
        adjustment = self.env["seyal.stock.move"].search([
            ("product_id", "=", self.product.id), ("move_type", "=", "adjustment_out"),
        ])
        self.assertEqual(len(adjustment), 1)
        self.assertEqual(adjustment.qty, 15)
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.warehouse.id), 35,
        )

    def test_validate_with_no_difference_creates_no_move(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        self.env["seyal.stock.inventory.line"].create({
            "inventory_id": inventory.id, "product_id": self.product.id, "counted_qty": 50,
        })
        moves_before = self.env["seyal.stock.move"].search_count([])
        inventory.action_validate()
        moves_after = self.env["seyal.stock.move"].search_count([])
        self.assertEqual(moves_before, moves_after)

    def test_cannot_validate_without_lines(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        with self.assertRaises(UserError):
            inventory.action_validate()

    def test_cannot_validate_twice(self):
        inventory = self.env["seyal.stock.inventory"].create({"warehouse_id": self.warehouse.id})
        self.env["seyal.stock.inventory.line"].create({
            "inventory_id": inventory.id, "product_id": self.product.id, "counted_qty": 50,
        })
        inventory.action_validate()
        with self.assertRaises(UserError):
            inventory.action_validate()
