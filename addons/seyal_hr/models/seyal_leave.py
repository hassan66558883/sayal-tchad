from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalLeave(models.Model):
    _name = "seyal.leave"
    _description = "Conge/Absence SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "date_start desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.leave") or "/",
    )
    employee_id = fields.Many2one("seyal.employee", string="Employe", required=True, tracking=True)
    leave_type = fields.Selection(
        [
            ("conge_paye", "Conge paye"),
            ("maladie", "Maladie"),
            ("absence_non_justifiee", "Absence non justifiee"),
            ("autre", "Autre"),
        ],
        string="Type", required=True, default="conge_paye", tracking=True,
    )
    date_start = fields.Date(string="Date de debut", required=True)
    date_end = fields.Date(string="Date de fin", required=True)
    days = fields.Integer(string="Nombre de jours", compute="_compute_days", store=True)
    reason = fields.Text(string="Motif")
    state = fields.Selection(
        [("draft", "Demande"), ("approved", "Approuve"), ("refused", "Refuse")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du conge doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.depends("date_start", "date_end")
    def _compute_days(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                rec.days = (rec.date_end - rec.date_start).days + 1
            else:
                rec.days = 0

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError("La date de fin doit etre posterieure ou egale a la date de debut.")

    def action_approve(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une demande peut etre approuvee.")
            rec.state = "approved"

    def action_refuse(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une demande peut etre refusee.")
            rec.state = "refused"
