from odoo.tests.common import TransactionCase


class TestSeyalPartnerBranchSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.branch_a = self.env["seyal.branch"].create({"name": "Agence Partner Secu A", "code": "APSA"})
        self.branch_b = self.env["seyal.branch"].create({"name": "Agence Partner Secu B", "code": "APSB"})
        self.partner_a = self.env["seyal.partner"].create({
            "name": "Client Agence A", "is_customer": True, "branch_id": self.branch_a.id,
        })
        self.partner_b = self.env["seyal.partner"].create({
            "name": "Client Agence B", "is_customer": True, "branch_id": self.branch_b.id,
        })

    def _make_responsable(self, login, branches):
        group = self.env.ref("seyal_security.group_seyal_responsable_agence")
        return self.env["res.users"].with_context(no_reset_password=True).create({
            "name": login, "login": login, "email": "%s@example.com" % login,
            "groups_id": [(6, 0, [group.id])],
            "seyal_branch_ids": [(6, 0, branches.ids)] if branches else [(5, 0, 0)],
        })

    def test_responsable_sees_only_own_branch_partners(self):
        user = self._make_responsable("resp_partner_a", self.branch_a)
        partners = self.env["seyal.partner"].with_user(user).search([])
        self.assertEqual(partners, self.partner_a)

    def test_responsable_without_branch_sees_nothing(self):
        user = self._make_responsable("resp_partner_none", self.env["seyal.branch"])
        partners = self.env["seyal.partner"].with_user(user).search([])
        self.assertFalse(partners)

    def test_ventes_role_unaffected(self):
        group = self.env.ref("seyal_security.group_seyal_ventes")
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Ventes Secu", "login": "ventes_secu", "email": "ventes_secu@example.com",
            "groups_id": [(6, 0, [group.id])],
        })
        partners = self.env["seyal.partner"].with_user(user).search([])
        self.assertIn(self.partner_a, partners)
        self.assertIn(self.partner_b, partners)
