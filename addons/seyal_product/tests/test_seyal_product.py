from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalProduct(TransactionCase):
    def setUp(self):
        super().setUp()
        self.uom_categ = self.env["seyal.uom.category"].create({"name": "Poids produit"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme produit", "category_id": self.uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.sac = self.env["seyal.uom"].create({
            "name": "Sac produit", "category_id": self.uom_categ.id, "is_reference": False, "factor": 50.0,
        })

    def test_create_product_generates_reference(self):
        product = self.env["seyal.product"].create({"name": "Ciment", "uom_id": self.kg.id})
        self.assertTrue(product.reference)
        self.assertTrue(product.reference.startswith("PRD"))

    @mute_logger("odoo.sql_db")
    def test_duplicate_barcode_raises(self):
        self.env["seyal.product"].create({"name": "P1", "uom_id": self.kg.id, "barcode": "123456"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.product"].create({"name": "P2", "uom_id": self.kg.id, "barcode": "123456"})

    def test_uom_po_defaults_to_uom_on_onchange(self):
        product = self.env["seyal.product"].new({"uom_id": self.kg.id})
        product._onchange_uom_id()
        self.assertEqual(product.uom_po_id, self.kg)

    def test_uom_po_must_share_category_with_uom(self):
        other_categ = self.env["seyal.uom.category"].create({"name": "Volume produit"})
        litre = self.env["seyal.uom"].create({
            "name": "Litre produit", "category_id": other_categ.id, "is_reference": True, "factor": 1.0,
        })
        with self.assertRaises(ValidationError):
            self.env["seyal.product"].create({
                "name": "Produit invalide", "uom_id": self.kg.id, "uom_po_id": litre.id,
            })

    def test_default_company_is_seyal(self):
        product = self.env["seyal.product"].create({"name": "Sucre", "uom_id": self.kg.id})
        self.assertEqual(product.company_id, self.env.ref("seyal_base.seyal_company"))

    def test_create_writes_audit_log(self):
        product = self.env["seyal.product"].create({"name": "Farine", "uom_id": self.kg.id})
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.product"), ("res_id", "=", product.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)

    def test_price_fields_default_to_zero(self):
        product = self.env["seyal.product"].create({"name": "Huile", "uom_id": self.kg.id})
        self.assertEqual(product.purchase_price, 0.0)
        self.assertEqual(product.cost_price, 0.0)
        self.assertEqual(product.sale_price, 0.0)
        self.assertEqual(product.wholesale_price, 0.0)
        self.assertEqual(product.retail_price, 0.0)
