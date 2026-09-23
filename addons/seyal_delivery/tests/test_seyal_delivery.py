import base64

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalDelivery(TransactionCase):
    def setUp(self):
        super().setUp()
        self.driver = self.env["seyal.driver"].create({"name": "Chauffeur Livraison"})
        self.vehicle = self.env["seyal.vehicle"].create({"name": "Camion Livraison", "plate_number": "TCH-LIV"})
        self.customer = self.env["seyal.partner"].create({"name": "Client Livraison", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids livraison"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme livraison", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit livraison", "uom_id": self.kg.id})
        self.order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id})
        self.env["seyal.sale.order.line"].create({
            "order_id": self.order.id, "product_id": self.product.id, "qty": 20, "unit_price": 100.0,
        })
        self.order.action_confirm()
        self.route = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver.id, "vehicle_id": self.vehicle.id,
        })

    def _make_delivery(self):
        return self.env["seyal.delivery"].create({
            "route_id": self.route.id, "sale_order_id": self.order.id,
        })

    def test_create_delivery_generates_reference_and_lines(self):
        delivery = self._make_delivery()
        self.assertTrue(delivery.reference.startswith("LIV"))
        self.assertEqual(len(delivery.line_ids), 1)
        self.assertEqual(delivery.line_ids.ordered_qty, 20)
        self.assertEqual(delivery.line_ids.delivered_qty, 20)

    def test_cannot_confirm_planifiee_delivery(self):
        delivery = self._make_delivery()
        delivery.signature = base64.b64encode(b"sig")
        with self.assertRaises(UserError):
            delivery.action_confirm_delivery()

    def test_cannot_confirm_without_signature(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        with self.assertRaises(UserError):
            delivery.action_confirm_delivery()

    def test_full_delivery_confirms_as_livree(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()
        self.assertEqual(delivery.state, "livree")
        self.assertTrue(delivery.delivery_datetime)

    def test_partial_delivery_confirms_as_partielle(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        delivery.line_ids.write({"delivered_qty": 5})
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()
        self.assertEqual(delivery.state, "partielle")

    def test_zero_delivered_confirms_as_probleme(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        delivery.line_ids.write({"delivered_qty": 0})
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()
        self.assertEqual(delivery.state, "probleme")

    def test_report_issue_requires_description(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        with self.assertRaises(UserError):
            delivery.action_report_issue()

    def test_report_issue_sets_state(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        delivery.issue_description = "Client absent"
        delivery.action_report_issue()
        self.assertEqual(delivery.state, "probleme")
        self.assertTrue(delivery.delivery_datetime)

    def test_cannot_report_issue_on_delivered(self):
        delivery = self._make_delivery()
        self.route.action_charger()
        delivery.signature = base64.b64encode(b"sig")
        delivery.action_confirm_delivery()
        delivery.issue_description = "Trop tard"
        with self.assertRaises(UserError):
            delivery.action_report_issue()

    def test_create_writes_audit_log(self):
        delivery = self._make_delivery()
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.delivery"), ("res_id", "=", delivery.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)
