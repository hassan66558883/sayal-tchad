from odoo import fields, models


class SeyalUomCategory(models.Model):
    _name = "seyal.uom.category"
    _description = "Categorie d'unite de mesure SEYAL-TCHAD"
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    active = fields.Boolean(default=True)
