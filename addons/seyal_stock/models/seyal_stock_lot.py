from odoo import fields, models


class SeyalStockLot(models.Model):
    _name = "seyal.stock.lot"
    _description = "Lot SEYAL-TCHAD"
    _order = "name"

    name = fields.Char(string="Numero de lot", required=True)
    product_id = fields.Many2one("seyal.product", string="Produit", required=True)
    production_date = fields.Date(string="Date de production")
    expiry_date = fields.Date(string="Date de peremption")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("name_product_unique", "unique(name, product_id)",
         "Ce numero de lot existe deja pour ce produit."),
    ]
