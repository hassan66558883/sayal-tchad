from odoo import api, fields, models


class SeyalBranch(models.Model):
    _name = "seyal.branch"
    _description = "Agence SEYAL-TCHAD"
    _order = "name"

    name = fields.Char(string="Nom de l'agence", required=True)
    code = fields.Char(string="Code", required=True, copy=False)
    address = fields.Char(string="Adresse")
    city = fields.Char(string="Ville")
    phone = fields.Char(string="Telephone")
    manager_id = fields.Many2one("res.users", string="Responsable d'agence")
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code de l'agence doit etre unique."),
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.code}] {rec.name}" if rec.code else rec.name
