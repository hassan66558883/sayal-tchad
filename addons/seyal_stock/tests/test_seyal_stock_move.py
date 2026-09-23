from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalStockMove(TransactionCase):
    def setUp(self):
        super().setUp()
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids move"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme move", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit move", "uom_id": self.kg.id})
        self.wh_a = self.env["seyal.warehouse"].create({"name": "Entrepot A move", "code": "WHM-A"})
        self.wh_b = self.env["seyal.warehouse"].create({"name": "Entrepot B move", "code": "WHM-B"})

    def test_create_in_move_and_validate(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        self.assertEqual(move.state, "draft")
        move.action_validate()
        self.assertEqual(move.state, "done")
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.wh_a.id), 10,
        )

    def test_in_move_requires_dest_only(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.stock.move"].create({
                "product_id": self.product.id, "qty": 10, "move_type": "in",
                "dest_warehouse_id": self.wh_a.id, "source_warehouse_id": self.wh_b.id,
            })

    def test_out_move_requires_source_only(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.stock.move"].create({
                "product_id": self.product.id, "qty": 10, "move_type": "out",
            })

    def test_transfer_requires_two_different_warehouses(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.stock.move"].create({
                "product_id": self.product.id, "qty": 10, "move_type": "transfer",
                "source_warehouse_id": self.wh_a.id, "dest_warehouse_id": self.wh_a.id,
            })

    def test_transfer_moves_stock_between_warehouses(self):
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 20, "move_type": "in",
            "dest_warehouse_id": self.wh_a.id, "state": "done",
        })
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 8, "move_type": "transfer",
            "source_warehouse_id": self.wh_a.id, "dest_warehouse_id": self.wh_b.id, "state": "done",
        })
        Move = self.env["seyal.stock.move"]
        self.assertEqual(Move.get_qty_on_hand(self.product.id, self.wh_a.id), 12)
        self.assertEqual(Move.get_qty_on_hand(self.product.id, self.wh_b.id), 8)
        self.assertEqual(Move.get_qty_on_hand(self.product.id), 20)

    def test_out_move_decreases_stock(self):
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 20, "move_type": "in",
            "dest_warehouse_id": self.wh_a.id, "state": "done",
        })
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 5, "move_type": "out",
            "source_warehouse_id": self.wh_a.id, "state": "done",
        })
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.wh_a.id), 15,
        )

    def test_draft_move_does_not_count_toward_stock(self):
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.wh_a.id), 0,
        )

    def test_done_move_is_immutable(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        move.action_validate()
        with self.assertRaises(UserError):
            move.write({"qty": 999})

    def test_done_move_reason_still_editable(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        move.action_validate()
        move.write({"reason": "Commentaire ajoute apres coup"})
        self.assertEqual(move.reason, "Commentaire ajoute apres coup")

    def test_cannot_validate_twice(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        move.action_validate()
        with self.assertRaises(UserError):
            move.action_validate()

    def test_cannot_cancel_done_move(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        move.action_validate()
        with self.assertRaises(UserError):
            move.action_cancel()

    def test_create_writes_audit_log(self):
        move = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in", "dest_warehouse_id": self.wh_a.id,
        })
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.stock.move"), ("res_id", "=", move.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)
