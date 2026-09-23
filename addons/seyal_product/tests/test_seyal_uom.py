from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalUom(TransactionCase):
    def setUp(self):
        super().setUp()
        self.categ = self.env["seyal.uom.category"].create({"name": "Poids test"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme test", "category_id": self.categ.id, "is_reference": True, "factor": 1.0,
        })
        self.sac = self.env["seyal.uom"].create({
            "name": "Sac 50kg test", "category_id": self.categ.id, "is_reference": False, "factor": 50.0,
        })

    def test_one_sac_is_50_kg(self):
        self.assertEqual(self.sac.convert_qty(1, self.kg), 50.0)

    def test_100_kg_is_2_sacs(self):
        self.assertEqual(self.kg.convert_qty(100, self.sac), 2.0)

    def test_cannot_convert_across_categories(self):
        other_categ = self.env["seyal.uom.category"].create({"name": "Volume test"})
        litre = self.env["seyal.uom"].create({
            "name": "Litre test", "category_id": other_categ.id, "is_reference": True, "factor": 1.0,
        })
        with self.assertRaises(ValidationError):
            self.kg.convert_qty(1, litre)

    def test_only_one_reference_per_category(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.uom"].create({
                "name": "Autre reference", "category_id": self.categ.id, "is_reference": True, "factor": 1.0,
            })

    def test_demo_data_sac_50kg(self):
        kg = self.env.ref("seyal_product.uom_kg")
        sac = self.env.ref("seyal_product.uom_sac_50kg")
        self.assertEqual(sac.convert_qty(1, kg), 50.0)
