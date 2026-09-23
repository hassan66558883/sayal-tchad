from odoo.tests.common import TransactionCase


class TestSeyalWarehouseSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wh_a = self.env["seyal.warehouse"].create({"name": "Entrepot Secu A", "code": "WH-SECA"})
        self.wh_b = self.env["seyal.warehouse"].create({"name": "Entrepot Secu B", "code": "WH-SECB"})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids securite entrepot"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme securite entrepot", "category_id": uom_categ.id,
            "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit securite entrepot", "uom_id": self.kg.id})

    def _make_stock_user(self, login, warehouses):
        group = self.env.ref("seyal_security.group_seyal_stock")
        return self.env["res.users"].with_context(no_reset_password=True).create({
            "name": login, "login": login, "email": "%s@example.com" % login,
            "groups_id": [(6, 0, [group.id])],
            "seyal_warehouse_ids": [(6, 0, warehouses.ids)] if warehouses else [(5, 0, 0)],
        })

    def test_user_sees_only_own_warehouse(self):
        user = self._make_stock_user("stock_a", self.wh_a)
        warehouses = self.env["seyal.warehouse"].with_user(user).search([])
        self.assertEqual(warehouses, self.wh_a)

    def test_user_without_warehouse_sees_nothing(self):
        user = self._make_stock_user("stock_none", self.env["seyal.warehouse"])
        warehouses = self.env["seyal.warehouse"].with_user(user).search([])
        self.assertFalse(warehouses)

    def test_user_sees_only_moves_touching_own_warehouse(self):
        user = self._make_stock_user("stock_moves", self.wh_a)
        move_a = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in",
            "dest_warehouse_id": self.wh_a.id, "state": "done",
        })
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 10, "move_type": "in",
            "dest_warehouse_id": self.wh_b.id, "state": "done",
        })
        moves = self.env["seyal.stock.move"].with_user(user).search([])
        self.assertEqual(moves, move_a)

    def test_user_sees_transfer_touching_own_warehouse_as_source_or_dest(self):
        user = self._make_stock_user("stock_transfer", self.wh_b)
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 20, "move_type": "in",
            "dest_warehouse_id": self.wh_a.id, "state": "done",
        })
        transfer = self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 5, "move_type": "transfer",
            "source_warehouse_id": self.wh_a.id, "dest_warehouse_id": self.wh_b.id, "state": "done",
        })
        moves = self.env["seyal.stock.move"].with_user(user).search([])
        self.assertEqual(moves, transfer)

    def test_user_sees_only_inventory_of_own_warehouse(self):
        user = self._make_stock_user("stock_inventory", self.wh_a)
        inventory_a = self.env["seyal.stock.inventory"].create({"warehouse_id": self.wh_a.id})
        self.env["seyal.stock.inventory"].create({"warehouse_id": self.wh_b.id})
        inventories = self.env["seyal.stock.inventory"].with_user(user).search([])
        self.assertEqual(inventories, inventory_a)

    def test_admin_unaffected_by_warehouse_rule(self):
        admin = self.env.ref("base.user_admin")
        warehouses = self.env["seyal.warehouse"].with_user(admin).search([])
        self.assertIn(self.wh_a, warehouses)
        self.assertIn(self.wh_b, warehouses)
