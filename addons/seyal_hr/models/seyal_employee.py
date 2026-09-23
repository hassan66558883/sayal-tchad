from odoo import api, fields, models


class SeyalEmployee(models.Model):
    _name = "seyal.employee"
    _description = "Employe SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "name"

    reference = fields.Char(
        string="Matricule", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.employee") or "/",
    )
    name = fields.Char(string="Nom", required=True, tracking=True)
    job_position_id = fields.Many2one("seyal.job.position", string="Poste", tracking=True)
    department_id = fields.Many2one("seyal.department", string="Departement", tracking=True)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    user_id = fields.Many2one("res.users", string="Utilisateur lie", copy=False)
    phone = fields.Char(string="Telephone")
    email = fields.Char(string="Email")
    hire_date = fields.Date(string="Date d'embauche", default=fields.Date.context_today)
    salary = fields.Float(string="Salaire de base")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "Le matricule doit etre unique."),
    ]

    @api.depends("reference", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.reference}] {rec.name}" if rec.reference and rec.reference != "/" else rec.name
