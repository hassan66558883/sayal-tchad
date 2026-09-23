from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalSupplierBill(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Facture", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids FRN"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme FRN", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit FRN", "uom_id": self.kg.id})

    def _make_bill(self, with_line=True, qty=10, unit_price=100.0):
        bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        if with_line:
            self.env["seyal.supplier.bill.line"].create({
                "bill_id": bill.id, "product_id": self.product.id, "qty": qty, "unit_price": unit_price,
            })
        return bill

    def test_create_bill_generates_reference(self):
        bill = self._make_bill()
        self.assertTrue(bill.reference.startswith("FRN"))

    def test_cannot_validate_without_lines(self):
        bill = self._make_bill(with_line=False)
        with self.assertRaises(UserError):
            bill.action_validate()

    def test_validate_workflow(self):
        bill = self._make_bill()
        bill.action_validate()
        self.assertEqual(bill.state, "validated")
        self.assertEqual(bill.amount_total, 1000.0)
        self.assertEqual(bill.amount_due, 1000.0)
        self.assertEqual(bill.payment_state, "not_paid")

    def test_cannot_cancel_paid_bill(self):
        bill = self._make_bill()
        bill.action_validate()
        payment = self.env["seyal.supplier.payment"].create({"bill_id": bill.id, "amount": 1000.0})
        payment.action_confirm()
        with self.assertRaises(UserError):
            bill.action_cancel()

    def test_create_writes_audit_log(self):
        bill = self._make_bill()
        entry = self.env["seyal.audit.log"].search([
            ("model_name", "=", "seyal.supplier.bill"), ("res_id", "=", bill.id), ("action", "=", "create"),
        ])
        self.assertEqual(len(entry), 1)
