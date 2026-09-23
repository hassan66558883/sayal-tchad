from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env["seyal.partner"].create({"name": "Client Facture", "is_customer": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids FAC"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme FAC", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit facture", "uom_id": self.kg.id})

    def _make_invoice(self, with_line=True, qty=10, unit_price=100.0):
        invoice = self.env["seyal.invoice"].create({"customer_id": self.customer.id})
        if with_line:
            self.env["seyal.invoice.line"].create({
                "invoice_id": invoice.id, "product_id": self.product.id, "qty": qty, "unit_price": unit_price,
            })
        return invoice

    def test_create_invoice_generates_reference(self):
        invoice = self._make_invoice()
        self.assertTrue(invoice.reference.startswith("FAC"))

    def test_cannot_validate_without_lines(self):
        invoice = self._make_invoice(with_line=False)
        with self.assertRaises(UserError):
            invoice.action_validate()

    def test_validate_workflow(self):
        invoice = self._make_invoice()
        invoice.action_validate()
        self.assertEqual(invoice.state, "validated")
        self.assertEqual(invoice.payment_state, "not_paid")
        self.assertEqual(invoice.amount_due, 1000.0)

    def test_cannot_validate_twice(self):
        invoice = self._make_invoice()
        invoice.action_validate()
        with self.assertRaises(UserError):
            invoice.action_validate()

    def test_credit_note_reduces_balance_sign(self):
        invoice = self._make_invoice(qty=10, unit_price=100.0)
        invoice.action_validate()
        credit_note = self.env["seyal.invoice"].create({
            "customer_id": self.customer.id, "move_type": "credit_note", "origin_invoice_id": invoice.id,
        })
        self.env["seyal.invoice.line"].create({
            "invoice_id": credit_note.id, "product_id": self.product.id, "qty": 2, "unit_price": 100.0,
        })
        credit_note.action_validate()
        self.assertEqual(self.customer.balance, 1000.0 - 200.0)

    def test_cannot_cancel_paid_invoice(self):
        invoice = self._make_invoice(qty=10, unit_price=100.0)
        invoice.action_validate()
        payment = self.env["seyal.payment"].create({"invoice_id": invoice.id, "amount": 1000.0})
        payment.action_confirm()
        with self.assertRaises(UserError):
            invoice.action_cancel()

    def test_create_writes_audit_log(self):
        invoice = self._make_invoice()
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.invoice"), ("res_id", "=", invoice.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)
