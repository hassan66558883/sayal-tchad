from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalSalesTarget(models.Model):
    _name = "seyal.sales.target"
    _description = "Objectif commercial SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "period_start desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.sales.target") or "/",
    )
    salesperson_id = fields.Many2one("res.users", string="Commercial", required=True, tracking=True)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    period_start = fields.Date(string="Debut de periode", required=True)
    period_end = fields.Date(string="Fin de periode", required=True)
    target_amount = fields.Float(string="Objectif", required=True)
    achieved_amount = fields.Float(string="Realise", readonly=True)
    achievement_rate = fields.Float(string="Taux de realisation (%)", readonly=True)

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de l'objectif doit etre unique."),
        ("target_positive", "CHECK(target_amount > 0)", "L'objectif doit etre strictement positif."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.constrains("period_start", "period_end")
    def _check_dates(self):
        for rec in self:
            if rec.period_end < rec.period_start:
                raise ValidationError("La date de fin doit etre posterieure ou egale a la date de debut.")

    def action_compute(self):
        for rec in self:
            orders = self.env["seyal.sale.order"].search([
                ("salesperson_id", "=", rec.salesperson_id.id),
                ("order_date", ">=", rec.period_start),
                ("order_date", "<=", rec.period_end),
                ("state", "in", ("confirmed", "done")),
            ])
            rec.achieved_amount = sum(orders.mapped("amount_total"))
            rec.achievement_rate = (rec.achieved_amount / rec.target_amount * 100) if rec.target_amount else 0.0
