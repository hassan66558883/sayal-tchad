from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSeyalCommissionRule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Commercial Rule", "login": "commercial_rule", "email": "commercial_rule@example.com",
        })

    def test_create_rule(self):
        rule = self.env["seyal.commission.rule"].create({"name": "Regle test", "rate_percent": 5.0})
        self.assertTrue(rule.active)

    def test_cannot_have_two_default_rules(self):
        self.env["seyal.commission.rule"].create({"name": "Regle par defaut", "rate_percent": 2.0})
        with self.assertRaises(ValidationError):
            self.env["seyal.commission.rule"].create({"name": "Autre regle par defaut", "rate_percent": 3.0})

    def test_cannot_have_two_rules_for_same_salesperson(self):
        self.env["seyal.commission.rule"].create({
            "name": "Regle A", "salesperson_id": self.user.id, "rate_percent": 5.0,
        })
        with self.assertRaises(ValidationError):
            self.env["seyal.commission.rule"].create({
                "name": "Regle B", "salesperson_id": self.user.id, "rate_percent": 7.0,
            })

    def test_rate_must_be_in_range(self):
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.commission.rule"].create({"name": "Regle invalide", "rate_percent": 150.0})
