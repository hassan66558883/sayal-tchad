from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestResUsersLogAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.dg_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Direction Log", "login": "direction_log", "email": "direction_log@example.com",
            "groups_id": [(6, 0, [self.env.ref("seyal_security.group_seyal_direction_generale").id])],
        })
        self.achats_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Achats Log", "login": "achats_log", "email": "achats_log@example.com",
            "groups_id": [(6, 0, [self.env.ref("seyal_security.group_seyal_achats").id])],
        })

    def test_direction_generale_can_read_login_history(self):
        # Should not raise: Direction generale is explicitly granted read
        # access to res.users.log by this module's ir.model.access.csv.
        self.env["res.users.log"].with_user(self.dg_user).search([])

    def test_other_role_cannot_read_login_history(self):
        with self.assertRaises(AccessError):
            self.env["res.users.log"].with_user(self.achats_user).search([])

    def test_admin_can_read_login_history(self):
        admin = self.env.ref("base.user_admin")
        self.env["res.users.log"].with_user(admin).search([])
