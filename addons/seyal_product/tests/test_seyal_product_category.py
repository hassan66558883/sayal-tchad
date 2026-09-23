from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalProductCategory(TransactionCase):
    def test_create_category(self):
        category = self.env["seyal.product.category"].create({"name": "Alimentation", "code": "ALIM"})
        self.assertEqual(category.complete_name, "Alimentation")

    def test_complete_name_includes_parent(self):
        parent = self.env["seyal.product.category"].create({"name": "Alimentation", "code": "ALIM2"})
        child = self.env["seyal.product.category"].create({
            "name": "Riz", "code": "RIZ", "parent_id": parent.id,
        })
        self.assertEqual(child.complete_name, "Alimentation / Riz")

    @mute_logger("odoo.sql_db")
    def test_code_must_be_unique(self):
        self.env["seyal.product.category"].create({"name": "Cat A", "code": "CA"})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.product.category"].create({"name": "Cat B", "code": "CA"})

    def test_category_cannot_be_its_own_ancestor(self):
        category = self.env["seyal.product.category"].create({"name": "Cat C", "code": "CC"})
        with self.assertRaises(ValidationError):
            category.write({"parent_id": category.id})
