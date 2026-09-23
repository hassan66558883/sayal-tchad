from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalPayslip(models.Model):
    _name = "seyal.payslip"
    _description = "Bulletin de salaire SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "period_start desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.payslip") or "/",
    )
    employee_id = fields.Many2one("seyal.employee", string="Employe", required=True, tracking=True)
    period_start = fields.Date(string="Debut de periode", required=True)
    period_end = fields.Date(string="Fin de periode", required=True)
    base_salary = fields.Float(string="Salaire de base", required=True)
    advance_ids = fields.One2many("seyal.advance", "payslip_id", string="Avances deduites")
    advances_deducted = fields.Float(string="Avances deduites", compute="_compute_net_salary", store=True)
    net_salary = fields.Float(string="Salaire net", compute="_compute_net_salary", store=True)
    state = fields.Selection(
        [("draft", "Brouillon"), ("validated", "Validee"), ("paid", "Payee")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du bulletin doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.depends("base_salary", "advance_ids.amount")
    def _compute_net_salary(self):
        for rec in self:
            rec.advances_deducted = sum(rec.advance_ids.mapped("amount"))
            rec.net_salary = rec.base_salary - rec.advances_deducted

    @api.constrains("period_start", "period_end")
    def _check_dates(self):
        for rec in self:
            if rec.period_end < rec.period_start:
                raise ValidationError("La date de fin doit etre posterieure ou egale a la date de debut.")

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        if self.employee_id:
            self.base_salary = self.employee_id.salary

    def action_validate(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un bulletin en brouillon peut etre valide.")
            advances = self.env["seyal.advance"].search([
                ("employee_id", "=", rec.employee_id.id),
                ("state", "=", "approved"),
                ("payslip_id", "=", False),
                ("advance_date", ">=", rec.period_start),
                ("advance_date", "<=", rec.period_end),
            ])
            advances.write({"payslip_id": rec.id})
            rec.state = "validated"

    def action_mark_paid(self):
        for rec in self:
            if rec.state != "validated":
                raise UserError("Seul un bulletin valide peut etre marque paye.")
            rec.state = "paid"
