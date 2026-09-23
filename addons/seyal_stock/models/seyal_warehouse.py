from odoo import fields, models


class SeyalWarehouse(models.Model):
    _name = "seyal.warehouse"
    _description = "Entrepot/Depot SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True, copy=False)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    address = fields.Char(string="Adresse")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code de l'entrepot doit etre unique."),
    ]
