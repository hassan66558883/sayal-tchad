from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalAttendance(models.Model):
    _name = "seyal.attendance"
    _description = "Presence SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "check_in desc"

    employee_id = fields.Many2one("seyal.employee", string="Employe", required=True)
    check_in = fields.Datetime(string="Entree", required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(string="Sortie")
    hours_worked = fields.Float(string="Heures travaillees", compute="_compute_hours_worked", store=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    @api.depends("check_in", "check_out")
    def _compute_hours_worked(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                rec.hours_worked = delta.total_seconds() / 3600.0
            else:
                rec.hours_worked = 0.0

    @api.constrains("check_in", "check_out")
    def _check_checkout_after_checkin(self):
        for rec in self:
            if rec.check_out and rec.check_out < rec.check_in:
                raise ValidationError("L'heure de sortie doit etre posterieure a l'heure d'entree.")
