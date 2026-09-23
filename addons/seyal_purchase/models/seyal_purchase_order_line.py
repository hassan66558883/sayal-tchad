from odoo import api, fields, models


class SeyalPurchaseOrderLine(models.Model):
    _name = "seyal.purchase.order.line"
    _description = "Ligne de commande d'achat SEYAL-TCHAD"
    _order = "id"

    order_id = fields.Many2one("seyal.purchase.order", string="Commande", required=True, ondelete="cascade")
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
