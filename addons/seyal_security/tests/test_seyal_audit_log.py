from odoo.tests.common import TransactionCase


class TestSeyalAuditLog(TransactionCase):
    def test_log_creates_entry(self):
        # seyal.branch inherits seyal.audit.mixin (Phase 12), so create()
        # already writes one automatic "create" entry; this test targets the
        # extra entry produced by the explicit log() call below, identified
        # by its distinctive description.
        branch = self.env["seyal.branch"].create({"name": "Agence Audit", "code": "AUD"})
        self.env["seyal.audit.log"].log("create", branch, description="test")
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.branch"), ("res_id", "=", branch.id),
            ("description", "=", "test"),
        ])
        self.assertEqual(len(entry), 1)
        self.assertEqual(entry.action, "create")
        self.assertEqual(entry.record_name, branch.display_name)

    def test_log_multiple_records(self):
        b1 = self.env["seyal.branch"].create({"name": "Agence 1", "code": "A1"})
        b2 = self.env["seyal.branch"].create({"name": "Agence 2", "code": "A2"})
        before = self.env["seyal.audit.log"].search_count([("model_name", "=", "seyal.branch")])
        self.env["seyal.audit.log"].log("write", b1 + b2)
        entries = self.env["seyal.audit.log"].search([("model_name", "=", "seyal.branch")])
        self.assertEqual(len(entries), before + 2)

    def test_log_without_user_context_defaults_to_current_user(self):
        branch = self.env["seyal.branch"].create({"name": "Agence Audit 2", "code": "AUD2"})
        self.env["seyal.audit.log"].log("create", branch)
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.branch"), ("res_id", "=", branch.id),
        ])
        self.assertEqual(entry.user_id, self.env.user)
