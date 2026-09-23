from odoo.tests.common import TransactionCase


class TestSeyalDeliverySecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Securite Livraison", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids securite livraison"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme securite livraison", "category_id": uom_categ.id,
            "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit securite livraison", "uom_id": self.kg.id})
        self.order = self.env["seyal.sale.order"].create({"customer_id": self.customer.id})
        self.env["seyal.sale.order.line"].create({
            "order_id": self.order.id, "product_id": self.product.id, "qty": 5, "unit_price": 10.0,
        })
        self.order.action_confirm()

        self.vehicle_a = self.env["seyal.vehicle"].create({"name": "Camion Sec A", "plate_number": "TCH-SECA"})
        self.vehicle_b = self.env["seyal.vehicle"].create({"name": "Camion Sec B", "plate_number": "TCH-SECB"})

        self.user_a = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Chauffeur A", "login": "chauffeur_a", "email": "chauffeur_a@example.com",
            "groups_id": [(6, 0, [self.env.ref("seyal_security.group_seyal_chauffeur").id])],
        })
        self.user_b = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Chauffeur B", "login": "chauffeur_b", "email": "chauffeur_b@example.com",
            "groups_id": [(6, 0, [self.env.ref("seyal_security.group_seyal_chauffeur").id])],
        })
        self.driver_a = self.env["seyal.driver"].create({"name": "Chauffeur A", "user_id": self.user_a.id})
        self.driver_b = self.env["seyal.driver"].create({"name": "Chauffeur B", "user_id": self.user_b.id})

        self.route_a = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver_a.id, "vehicle_id": self.vehicle_a.id,
        })
        self.route_b = self.env["seyal.delivery.route"].create({
            "driver_id": self.driver_b.id, "vehicle_id": self.vehicle_b.id,
        })
        self.delivery_a = self.env["seyal.delivery"].create({
            "route_id": self.route_a.id, "sale_order_id": self.order.id,
        })
        self.delivery_b = self.env["seyal.delivery"].create({
            "route_id": self.route_b.id, "sale_order_id": self.order.id,
        })

    def test_driver_sees_only_own_route(self):
        routes = self.env["seyal.delivery.route"].with_user(self.user_a).search([])
        self.assertEqual(routes, self.route_a)

    def test_driver_sees_only_own_delivery(self):
        deliveries = self.env["seyal.delivery"].with_user(self.user_a).search([])
        self.assertEqual(deliveries, self.delivery_a)

    def test_driver_b_does_not_see_driver_a_delivery(self):
        deliveries = self.env["seyal.delivery"].with_user(self.user_b).search([])
        self.assertNotIn(self.delivery_a, deliveries)
        self.assertEqual(deliveries, self.delivery_b)
