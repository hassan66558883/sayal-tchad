from odoo.tests.common import TransactionCase


class TestSeyalBranchAudit(TransactionCase):
    def test_branch_create_writes_audit_log(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Audit Phase12", "code": "AP12"})
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.branch"), ("res_id", "=", branch.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)

    def test_branch_write_writes_audit_log(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Audit Phase12 B", "code": "AP12B"})
        branch.write({"phone": "+235 60 00 00 00"})
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.branch"), ("res_id", "=", branch.id), ("action", "=", "write"),
        ])
        self.assertEqual(len(entry), 1)
