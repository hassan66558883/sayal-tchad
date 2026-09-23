from odoo.tests.common import TransactionCase


class TestSeyalPartnerPayableBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env["seyal.partner"].create({"name": "Fournisseur Solde", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids solde fournisseur"})
        self.kg = self.env["seyal.uom"].create({
            "name": "Kilogramme solde fournisseur", "category_id": uom_categ.id,
            "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit solde fournisseur", "uom_id": self.kg.id})

    def test_payable_balance_zero_with_no_bill(self):
        self.assertEqual(self.supplier.payable_balance, 0.0)

    def test_payable_balance_reflects_unpaid_bill(self):
        bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": bill.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        bill.action_validate()
        self.assertEqual(self.supplier.payable_balance, 1000.0)

    def test_payable_balance_decreases_after_payment(self):
        bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": bill.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        bill.action_validate()
        payment = self.env["seyal.supplier.payment"].create({"bill_id": bill.id, "amount": 400.0})
        payment.action_confirm()
        self.assertEqual(self.supplier.payable_balance, 600.0)

    def test_draft_bill_does_not_affect_payable_balance(self):
        bill = self.env["seyal.supplier.bill"].create({"supplier_id": self.supplier.id})
        self.env["seyal.supplier.bill.line"].create({
            "bill_id": bill.id, "product_id": self.product.id, "qty": 5, "unit_price": 200.0,
        })
        self.assertEqual(self.supplier.payable_balance, 0.0)
