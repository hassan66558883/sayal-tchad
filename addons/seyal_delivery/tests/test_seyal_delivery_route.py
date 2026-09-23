import base64

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalDeliveryRoute(TransactionCase):
    def setUp(self):
        super().setUp()
        self.driver = self.env["seyal.driver"].create({"name": "Chauffeur Route"})
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Route", "plate_number": "TCH-RTE"})
        self.customer = self.env["seyal.partner"].create({"name": "Client Route", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids route"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme route", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit route", "uom_id": self.kg.id})
        self.order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id})
        self.env["seyal.sale.order.line"].create({
            "order_id": self.order.id, "product_id": self.product.id, "qty": 10, "unit_price": 50.0,
        })
        self.order.action_confirm()

    def _make_route(self, with_delivery=True):
        route = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver.id, "vehicle_id": self.vehicle.id,
        })
        if with_delivery:
            self.env["seyal.delivery"].create({"route_id": route.id, "sale_order_id": self.order.id})
        return route

    def test_create_route_generates_reference(self):
        route = self._make_route()
        self.assertTrue(route.reference.startswith("TRN"))

    def test_cannot_charger_without_delivery(self):
        route = self._make_route(with_delivery=False)
        with self.assertRaises(UserError):
            route.action_charger()

    def test_full_route_workflow(self):
        route = self._make_route()
        route.action_charger()
        self.assertEqual(route.state, "chargee")
        route.action_demarrer()
        self.assertEqual(route.state, "en_livraison")

        delivery = route.delivery_ids
        delivery.line_ids.write({"delivered_qty": 10})
        delivery.signature = base64.b64encode(b"fake-signature-bytes")
        delivery.action_confirm_delivery()
        self.assertEqual(delivery.state, "livree")

        route.action_terminer()
        self.assertEqual(route.state, "livree")
        route.action_cloturer()
        self.assertEqual(route.state, "cloturee")

    def test_cannot_terminer_with_unfinished_delivery(self):
        route = self._make_route()
        route.action_charger()
        route.action_demarrer()
        with self.assertRaises(UserError):
            route.action_terminer()

    def test_cannot_skip_states(self):
        route = self._make_route()
        with self.assertRaises(UserError):
            route.action_demarrer()
        with self.assertRaises(UserError):
            route.action_terminer()
        with self.assertRaises(UserError):
            route.action_cloturer()
