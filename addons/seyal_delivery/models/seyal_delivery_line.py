from odoo import fields, models


class SeyalDeliveryLine(models.Model):
    _name = "seyal.delivery.line"
    _description = "Ligne de livraison SEYAL-TCHAD"
    _order = "id"

    delivery_id = fields.Many2one("seyal.delivery", string="Livraison", required=True, ondelete="cascade")
    product_id = fields.Many2one("seyal.product", string="Produit", required=True)
    ordered_qty = fields.Float(string="Quantite commandee", required=True)
    delivered_qty = fields.Float(string="Quantite livree", default=0.0)

    _sql_constraints = [
        ("ordered_qty_positive", "CHECK(ordered_qty > 0)", "La quantite commandee doit etre positive."),
        ("delivered_qty_non_negative", "CHECK(delivered_qty >= 0)",
         "La quantite livree ne peut pas etre negative."),
    ]
