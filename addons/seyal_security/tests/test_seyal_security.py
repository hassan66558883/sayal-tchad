from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestSeyalSecurityBranchRules(TransactionCase):
    def setUp(self):
        super().setUp()
        self.branch_a = self.env["seyal.branch"].create({"name": "Agence A", "code": "BR-A"})
        self.branch_b = self.env["seyal.branch"].create({"name": "Agence B", "code": "BR-B"})

    def _make_responsable(self, login, branches):
        group = self.env.ref("seyal_security.group_seyal_responsable_agence")
        return self.env["res.users"].with_context(no_reset_password=True).create({
            "name": login, "login": login, "email": "%s@example.com" % login,
            "groups_id": [(6, 0, [group.id])],
            "seyal_branch_ids": [(6, 0, branches.ids)] if branches else [(5, 0, 0)],
        })

    def test_responsable_sees_only_own_branch(self):
        user = self._make_responsable("respa", self.branch_a)
        branches = self.env["seyal.branch"].with_user(user).search([])
        self.assertEqual(branches, self.branch_a)

    def test_responsable_cannot_read_other_branch_directly(self):
        user = self._make_responsable("respa2", self.branch_a)
        with self.assertRaises(AccessError):
            self.branch_b.with_user(user).read(["name"])

    def test_responsable_without_assigned_branch_sees_nothing(self):
        user = self._make_responsable("respnone", self.env["seyal.branch"])
        branches = self.env["seyal.branch"].with_user(user).search([])
        self.assertFalse(branches)

    def test_responsable_with_two_branches_sees_both(self):
        user = self._make_responsable("respab", self.branch_a + self.branch_b)
        branches = self.env["seyal.branch"].with_user(user).search([])
        self.assertEqual(branches, self.branch_a + self.branch_b)

    def test_all_roles_created(self):
        role_xmlids = [
            "group_seyal_direction_generale", "group_seyal_achats", "group_seyal_ventes",
            "group_seyal_stock", "group_seyal_logistique", "group_seyal_chauffeur",
            "group_seyal_comptable", "group_seyal_caissier", "group_seyal_rh",
            "group_seyal_responsable_agence",
        ]
        for xmlid in role_xmlids:
            group = self.env.ref("seyal_security.%s" % xmlid)
            self.assertTrue(group.exists())
