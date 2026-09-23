from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalProductCategory(models.Model):
    _name = "seyal.product.category"
    _description = "Categorie de produit SEYAL-TCHAD"
    _order = "complete_name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", copy=False)
    parent_id = fields.Many2one("seyal.product.category", string="Categorie parente", ondelete="restrict")
    complete_name = fields.Char(string="Nom complet", compute="_compute_complete_name", store=True, recursive=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code de la categorie doit etre unique."),
    ]

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = f"{rec.parent_id.complete_name} / {rec.name}" if rec.parent_id else rec.name

    @api.constrains("parent_id")
    def _check_parent_not_recursive(self):
        if not self._check_recursion():
            raise ValidationError("Une categorie ne peut pas etre sa propre ancetre.")
