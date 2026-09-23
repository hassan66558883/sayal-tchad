from odoo import fields, models


class SeyalProductBrand(models.Model):
    _name = "seyal.product.brand"
    _description = "Marque de produit SEYAL-TCHAD"
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", copy=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code de la marque doit etre unique."),
    ]
