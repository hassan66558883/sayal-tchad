from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalCommission(models.Model):
    _name = "seyal.commission"
    _description = "Commission commerciale SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "period_start desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.commission") or "/",
    )
    salesperson_id = fields.Many2one("res.users", string="Commercial", required=True, tracking=True)
    period_start = fields.Date(string="Debut de periode", required=True)
    period_end = fields.Date(string="Fin de periode", required=True)
    rate_percent = fields.Float(string="Taux (%)", required=True)
    base_amount = fields.Float(
        string="Base de calcul (encaissements)", readonly=True,
        help="Somme des paiements clients confirmes, sur la periode, des commandes de ce commercial.",
    )
    commission_amount = fields.Float(string="Montant de la commission", readonly=True)
    state = fields.Selection(
        [("draft", "Brouillon"), ("validated", "Validee"), ("cancelled", "Annulee")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la commission doit etre unique."),
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

    @api.onchange("salesperson_id")
    def _onchange_salesperson_id(self):
        if self.salesperson_id:
            rule = self.env["seyal.commission.rule"].search([
                ("salesperson_id", "=", self.salesperson_id.id), ("active", "=", True),
            ], limit=1) or self.env["seyal.commission.rule"].search([
                ("salesperson_id", "=", False), ("active", "=", True),
            ], limit=1)
            if rule:
                self.rate_percent = rule.rate_percent

    def action_compute(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une commission en brouillon peut etre recalculee.")
            payments = self.env["seyal.payment"].search([
                ("state", "=", "confirmed"),
                ("payment_date", ">=", rec.period_start),
                ("payment_date", "<=", rec.period_end),
                ("invoice_id.sale_order_id.salesperson_id", "=", rec.salesperson_id.id),
            ])
            rec.base_amount = sum(payments.mapped("amount"))
            rec.commission_amount = rec.base_amount * rec.rate_percent / 100.0

    def action_validate(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une commission en brouillon peut etre validee.")
            rec.state = "validated"

    def action_cancel(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une commission en brouillon peut etre annulee.")
            rec.state = "cancelled"
