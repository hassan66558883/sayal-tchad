import base64

from odoo.tests.common import TransactionCase


class TestSeyalDeliveryStockIntegration(TransactionCase):
    def setUp(self):
        super().setUp()
        self.driver = self.env["seyal.driver"].create({"name": "Chauffeur Stock"})
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Stock", "plate_number": "TCH-STK"})
        self.customer = self.env["seyal.partner"].create({"name": "Client Stock", "is_customer": True})
        self.warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Livraison", "code": "WH-LIV"})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids stock delivery"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme stock delivery", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit stock delivery", "uom_id": self.kg.id})
        self.env["seyal.stock.move"].create({
            "product_id": self.product.id, "qty": 100, "move_type": "in",
            "dest_warehouse_id": self.warehouse.id, "state": "done",
        })
        self.order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id})
        self.env["seyal.sale.order.line"].create({
            "order_id": self.order.id, "product_id": self.product.id, "qty": 15, "unit_price": 100.0,
        })
        self.order.action_confirm()

    def test_confirming_delivery_creates_stock_out_move_when_warehouse_set(self):
        route = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver.id, "vehicle_id": self.vehicle.id, "warehouse_id": self.warehouse.id,
        })
        delivery = self.env["seyal.delivery"].create({"route_id": route.id, "sale_order_id": self.order.id})
        route.action_charger()
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()

        move = self.env["seyal.stock.move"].search([
            ("product_id", "=", self.product.id), ("move_type", "=", "out"),
        ])
        self.assertEqual(len(move), 1)
        self.assertEqual(move.qty, 15)
        self.assertEqual(move.source_warehouse_id, self.warehouse)
        self.assertEqual(move.state, "done")
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.warehouse.id), 85,
        )

    def test_no_stock_move_when_route_has_no_warehouse(self):
        route = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver.id, "vehicle_id": self.vehicle.id,
        })
        delivery = self.env["seyal.delivery"].create({"route_id": route.id, "sale_order_id": self.order.id})
        route.action_charger()
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()

        moves = self.env["seyal.stock.move"].search([
            ("product_id", "=", self.product.id), ("move_type", "=", "out"),
        ])
        self.assertFalse(moves)
        self.assertEqual(delivery.state, "livree")

    def test_partial_delivery_only_debits_delivered_qty(self):
        route = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver.id, "vehicle_id": self.vehicle.id, "warehouse_id": self.warehouse.id,
        })
        delivery = self.env["seyal.delivery"].create({"route_id": route.id, "sale_order_id": self.order.id})
        route.action_charger()
        delivery.line_ids.write({"delivered_qty": 10})
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()

        self.assertEqual(delivery.state, "partielle")
        move = self.env["seyal.stock.move"].search([
            ("product_id", "=", self.product.id), ("move_type", "=", "out"),
        ])
        self.assertEqual(move.qty, 10)
