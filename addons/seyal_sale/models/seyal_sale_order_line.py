from odoo import api, fields, models


class SeyalSaleOrderLine(models.Model):
    _name = "seyal.sale.order.line"
    _description = "Ligne de commande de vente SEYAL-TCHAD"
    _order = "id"

    order_id = fields.Many2one("seyal.sale.order", string="Commande", required=True, ondelete="cascade")
    product_id = fields.Many2one("seyal.product", string="Produit", required=True)
    qty = fields.Float(string="Quantite", required=True, default=1.0)
    unit_price = fields.Float(string="Prix unitaire", required=True)
    discount_percent = fields.Float(string="Remise (%)", default=0.0)
    subtotal = fields.Float(string="Sous-total", compute="_compute_subtotal", store=True)

    _sql_constraints = [
        ("qty_positive", "CHECK(qty > 0)", "La quantite doit etre strictement positive."),
        ("discount_range", "CHECK(discount_percent >= 0 AND discount_percent <= 100)",
         "La remise doit etre comprise entre 0 et 100%."),
    ]

    @api.depends("qty", "unit_price", "discount_percent")
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.unit_price * (1 - rec.discount_percent / 100.0)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            customer_type = self.order_id.customer_id.customer_type if self.order_id else False
            if customer_type == "grossiste" and self.product_id.wholesale_price:
                self.unit_price = self.product_id.wholesale_price
            elif customer_type in ("detaillant", "boutique", "supermarche") and self.product_id.retail_price:
                self.unit_price = self.product_id.retail_price
            else:
                self.unit_price = self.product_id.sale_price
