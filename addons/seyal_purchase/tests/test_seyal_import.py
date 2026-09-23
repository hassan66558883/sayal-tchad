from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Import", "is_supplier": True})
        self.uom_categ = self.env["seyal.uom.category"].create({"name": "Poids Import"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme Import", "category_id": self.uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product_a = self.env["seyal.product"].create({"name": "Sucre", "uom_id": self.kg.id})
        self.product_b = self.env["seyal.product"].create({"name": "Farine", "uom_id": self.kg.id})
        self.order = self.env["seyal.purchase.order"].create({
            "supplier_id": self.supplier.id, "is_import": True,
        })
        self.env["seyal.purchase.order.line"].create({
            "order_id": self.order.id, "product_id": self.product_a.id, "qty": 100, "unit_price": 10.0,
        })
        self.env["seyal.purchase.order.line"].create({
            "order_id": self.order.id, "product_id": self.product_b.id, "qty": 100, "unit_price": 30.0,
        })
        self.order.action_confirm()

    def test_create_import_generates_reference(self):
        imp = self.env["seyal.import"].create({"purchase_order_id": self.order.id})
        self.assertTrue(imp.reference.startswith("IMP"))

    def test_real_cost_formula(self):
        imp = self.env["seyal.import"].create({
            "purchase_order_id": self.order.id,
            "transport_cost": 500.0, "customs_cost": 300.0, "transit_cost": 100.0, "other_costs": 100.0,
        })
        # purchase_amount = 100*10 + 100*30 = 4000 ; extras = 500+300+100+100 = 1000
        self.assertEqual(imp.purchase_amount, 4000.0)
        self.assertEqual(imp.total_extra_costs, 1000.0)
        self.assertEqual(imp.real_cost, 5000.0)

    def test_state_transitions_must_be_sequential(self):
        imp = self.env["seyal.import"].create({"purchase_order_id": self.order.id})
        with self.assertRaises(UserError):
            imp.action_arrivee()
        with self.assertRaises(UserError):
            imp.action_douane()
        with self.assertRaises(UserError):
            imp.action_receptionner()
        imp.action_expedier()
        self.assertEqual(imp.state, "expedie")
        imp.action_arrivee()
        self.assertEqual(imp.state, "arrive")
        imp.action_douane()
        self.assertEqual(imp.state, "douane")
        imp.action_receptionner()
        self.assertEqual(imp.state, "receptionne")

    def test_reception_marks_purchase_order_done(self):
        imp = self.env["seyal.import"].create({"purchase_order_id": self.order.id})
        imp.action_expedier()
        imp.action_arrivee()
        imp.action_douane()
        imp.action_receptionner()
        self.assertEqual(self.order.state, "done")

    def test_reception_allocates_real_cost_to_products(self):
        imp = self.env["seyal.import"].create({
            "purchase_order_id": self.order.id,
            "transport_cost": 500.0, "customs_cost": 300.0, "transit_cost": 100.0, "other_costs": 100.0,
        })
        imp.action_expedier()
        imp.action_arrivee()
        imp.action_douane()
        imp.action_receptionner()
        # product_a: subtotal 1000 / total 4000 = 25% share -> allocated 250 -> (1000+250)/100 = 12.5
        # product_b: subtotal 3000 / total 4000 = 75% share -> allocated 750 -> (3000+750)/100 = 37.5
        self.assertAlmostEqual(self.product_a.cost_price, 12.5)
        self.assertAlmostEqual(self.product_b.cost_price, 37.5)

    def test_only_one_import_per_purchase_order(self):
        self.env["seyal.import"].create({"purchase_order_id": self.order.id})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.import"].create({"purchase_order_id": self.order.id})

    def test_purchase_order_domain_requires_is_import(self):
        non_import_order = self.env["seyal.purchase.order"].create({"supplier_id": self.supplier.id})
        self.env["seyal.purchase.order.line"].create({
            "order_id": non_import_order.id, "product_id": self.product_a.id, "qty": 1, "unit_price": 10.0,
        })
        # The domain on purchase_order_id is a UI-level filter, not a server
        # constraint - creating anyway must still succeed (Odoo domains
        # restrict what the form's selector proposes, not raw create()).
        imp = self.env["seyal.import"].create({"purchase_order_id": non_import_order.id})
        self.assertTrue(imp)
