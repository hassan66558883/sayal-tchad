from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSeyalPartner(TransactionCase):
    def test_create_customer_generates_reference(self):
        partner = self.env["seyal.partner"].create({
            "name": "Grossiste Ndjamena", "is_customer": True, "customer_type": "grossiste",
        })
        self.assertTrue(partner.reference)
        self.assertTrue(partner.reference.startswith("PAR"))

    def test_create_supplier(self):
        partner = self.env["seyal.partner"].create({"name": "Fournisseur Chine", "is_supplier": True})
        self.assertTrue(partner.is_supplier)
        self.assertFalse(partner.is_customer)

    def test_partner_can_be_both_customer_and_supplier(self):
        partner = self.env["seyal.partner"].create({
            "name": "Grossiste-Fournisseur", "is_customer": True, "is_supplier": True,
            "customer_type": "grossiste",
        })
        self.assertTrue(partner.is_customer)
        self.assertTrue(partner.is_supplier)

    def test_must_be_customer_or_supplier(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.partner"].create({"name": "Ni client ni fournisseur"})

    def test_customer_type_requires_is_customer(self):
        with self.assertRaises(ValidationError):
            self.env["seyal.partner"].create({
                "name": "Fournisseur avec type", "is_supplier": True, "customer_type": "grossiste",
            })

    @mute_logger("odoo.sql_db")
    def test_duplicate_reference_raises(self):
        p1 = self.env["seyal.partner"].create({"name": "Client 1", "is_customer": True})
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["seyal.partner"].create({
                    "name": "Client duplique", "is_customer": True, "reference": p1.reference,
                })

    def test_default_company_is_seyal(self):
        partner = self.env["seyal.partner"].create({"name": "Detaillant", "is_customer": True})
        self.assertEqual(partner.company_id, self.env.ref("seyal_base.seyal_company"))

    def test_create_writes_audit_log(self):
        partner = self.env["seyal.partner"].create({"name": "Boutique", "is_customer": True})
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.partner"), ("res_id", "=", partner.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)

    def test_branch_and_salesperson_assignment(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Test Partner", "code": "ATP"})
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Commercial Test", "login": "commercial_test", "email": "commercial_test@example.com",
        })
        partner = self.env["seyal.partner"].create({
            "name": "Supermarche X", "is_customer": True, "customer_type": "supermarche",
            "branch_id": branch.id, "salesperson_id": user.id, "credit_limit": 500000.0,
        })
        self.assertEqual(partner.branch_id, branch)
        self.assertEqual(partner.salesperson_id, user)
        self.assertEqual(partner.credit_limit, 500000.0)
