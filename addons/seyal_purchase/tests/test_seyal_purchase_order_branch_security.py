from odoo.tests.common import TransactionCase


class TestSeyalPurchaseOrderBranchSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.branch_a = self.env["seyal.branch"].create({"name": "Agence PO Secu A", "code": "APOSA"})
        self.branch_b = self.env["seyal.branch"].create({"name": "Agence PO Secu B", "code": "APOSB"})
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur PO Secu", "is_supplier": True})
        self.order_a = self.env["seyal.purchase.order"].create({
            "supplier_id": self.supplier.id, "branch_id": self.branch_a.id,
        })
        self.order_b = self.env["seyal.purchase.order"].create({
            "supplier_id": self.supplier.id, "branch_id": self.branch_b.id,
        })

    def _make_responsable(self, login, branches):
        group = self.env.ref("seyal_security.group_seyal_responsable_agence")
        return self.env["res.users"].with_context(no_reset_password=True).create({
            "name": login, "login": login, "email": "%s@example.com" % login,
            "groups_id": [(6, 0, [group.id])],
            "seyal_branch_ids": [(6, 0, branches.ids)] if branches else [(5, 0, 0)],
        })

    def test_responsable_sees_only_own_branch_orders(self):
        user = self._make_responsable("resp_po_a", self.branch_a)
        orders = self.env["seyal.purchase.order"].with_user(user).search([])
        self.assertEqual(orders, self.order_a)

    def test_responsable_without_branch_sees_nothing(self):
        user = self._make_responsable("resp_po_none", self.env["seyal.branch"])
        orders = self.env["seyal.purchase.order"].with_user(user).search([])
        self.assertFalse(orders)
