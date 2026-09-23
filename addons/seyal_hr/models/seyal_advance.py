from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalAdvance(models.Model):
    _name = "seyal.advance"
    _description = "Avance sur salaire SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "advance_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.advance") or "/",
    )
    employee_id = fields.Many2one("seyal.employee", string="Employe", required=True, tracking=True)
    advance_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Float(string="Montant", required=True)
    reason = fields.Char(string="Motif")
    state = fields.Selection(
        [("draft", "Demande"), ("approved", "Approuve"), ("cancelled", "Annule")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    payslip_id = fields.Many2one(
        "seyal.payslip", string="Bulletin de deduction", readonly=True, copy=False,
        help="Renseigne automatiquement lors de la validation du bulletin de salaire qui deduit cette avance.",
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de l'avance doit etre unique."),
        ("amount_positive", "CHECK(amount > 0)", "Le montant doit etre strictement positif."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    def action_approve(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une demande peut etre approuvee.")
            rec.state = "approved"

    def action_cancel(self):
        for rec in self:
            if rec.payslip_id:
                raise UserError("Impossible d'annuler une avance deja deduite sur un bulletin de salaire.")
            if rec.state == "cancelled":
                raise UserError("Cette avance est deja annulee.")
            rec.state = "cancelled"
