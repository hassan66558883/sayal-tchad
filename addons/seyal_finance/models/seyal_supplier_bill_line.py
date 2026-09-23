from odoo import api, fields, models


class SeyalSupplierBillLine(models.Model):
    _name = "seyal.supplier.bill.line"
    _description = "Ligne de facture fournisseur SEYAL-TCHAD"
    _order = "id"

    bill_id = fields.Many2one("seyal.supplier.bill", string="Facture", required=True, ondelete="cascade")
    product_id = fields.Many2one("seyal.product", string="Produit", required=True)
    qty = fields.Float(string="Quantite", required=True, default=1.0)
    unit_price = fields.Float(string="Prix unitaire", required=True)
    subtotal = fields.Float(string="Sous-total", compute="_compute_subtotal", store=True)

    _sql_constraints = [
        ("qty_positive", "CHECK(qty > 0)", "La quantite doit etre strictement positive."),
    ]

    @api.depends("qty", "unit_price")
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.unit_price
