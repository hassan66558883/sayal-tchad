from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSeyalStockReceptionWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        supplier = self.env["seyal.partner"].create({"name": "Fournisseur Wizard", "is_supplier": True})
        uom_categ = self.env["seyal.uom.category"].create({"name": "Poids wizard"})
        kg = self.env["seyal.uom"].create({
            "name": "Kilogramme wizard", "category_id": uom_categ.id, "is_reference": True, "factor": 1.0,
        })
        self.product = self.env["seyal.product"].create({"name": "Produit wizard", "uom_id": kg.id})
        self.warehouse = self.env["seyal.warehouse"].create({"name": "Entrepot Wizard", "code": "WH-WIZ"})
        order = self.env["seyal.purchase.order"].create({"supplier_id": supplier.id, "is_import": True})
        self.env["seyal.purchase.order.line"].create({
            "order_id": order.id, "product_id": self.product.id, "qty": 30, "unit_price": 100.0,
        })
        order.action_confirm()
        self.import_rec = self.env["seyal.import"].create({"purchase_order_id": order.id})

    def test_wizard_requires_receptionne_state(self):
        wizard = self.env["seyal.stock.reception.wizard"].create({
            "import_id": self.import_rec.id, "warehouse_id": self.warehouse.id,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_creates_draft_in_moves(self):
        self.import_rec.action_expedier()
        self.import_rec.action_arrivee()
        self.import_rec.action_douane()
        self.import_rec.action_receptionner()
        wizard = self.env["seyal.stock.reception.wizard"].create({
            "import_id": self.import_rec.id, "warehouse_id": self.warehouse.id,
        })
        wizard.action_confirm()
        moves = self.env["seyal.stock.move"].search([("origin_import_id", "=", self.import_rec.id)])
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves.state, "draft")
        self.assertEqual(moves.qty, 30)
        self.assertEqual(moves.dest_warehouse_id, self.warehouse)
        # Draft: not yet counted toward on-hand stock.
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.warehouse.id), 0,
        )
        moves.action_validate()
        self.assertEqual(
            self.env["seyal.stock.move"].get_qty_on_hand(self.product.id, self.warehouse.id), 30,
        )
