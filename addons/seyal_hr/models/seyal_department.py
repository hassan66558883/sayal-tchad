from odoo import fields, models


class SeyalDepartment(models.Model):
    _name = "seyal.department"
    _description = "Departement SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True, copy=False)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    manager_id = fields.Many2one("res.users", string="Responsable")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code du departement doit etre unique."),
    ]
