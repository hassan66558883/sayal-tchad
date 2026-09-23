from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalCashTransfer(models.Model):
    _name = "seyal.cash.transfer"
    _description = "Transfert Caisse <-> Banque SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "transfer_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.cash.transfer") or "/",
    )
    direction = fields.Selection(
        [("deposit", "Depot en banque"), ("withdrawal", "Retrait de banque")],
        string="Sens", required=True, default="deposit", tracking=True,
    )
    cash_account_id = fields.Many2one("seyal.cash.account", string="Caisse", required=True, tracking=True)
    bank_account_id = fields.Many2one("seyal.bank.account", string="Compte bancaire", required=True, tracking=True)
    transfer_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Float(string="Montant", required=True)
    state = fields.Selection(
        [("draft", "Brouillon"), ("confirmed", "Confirme"), ("cancelled", "Annule")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du transfert doit etre unique."),
        ("amount_positive", "CHECK(amount > 0)", "Le montant doit etre strictement positif."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un transfert en brouillon peut etre confirme.")
            if rec.direction == "deposit" and rec.amount > rec.cash_account_id.balance + 0.001:
                raise UserError("Solde de caisse insuffisant pour ce depot.")
            if rec.direction == "withdrawal" and rec.amount > rec.bank_account_id.balance + 0.001:
                raise UserError("Solde bancaire insuffisant pour ce retrait.")
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    "Seul un transfert en brouillon peut etre annule. Un transfert confirme est definitif."
                )
            rec.state = "cancelled"

    def write(self, vals):
        for rec in self:
            if rec.state == "confirmed":
                raise UserError("Un transfert confirme est immuable.")
        return super().write(vals)
