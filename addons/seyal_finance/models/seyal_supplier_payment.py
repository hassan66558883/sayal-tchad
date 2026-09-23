from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalSupplierPayment(models.Model):
    _name = "seyal.supplier.payment"
    _description = "Paiement fournisseur SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "payment_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.supplier.payment") or "/",
    )
    bill_id = fields.Many2one("seyal.supplier.bill", string="Facture fournisseur", required=True, tracking=True)
    supplier_id = fields.Many2one(related="bill_id.supplier_id", string="Fournisseur", store=True)
    payment_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Float(string="Montant", required=True)
    method = fields.Selection(
        [("cash", "Especes"), ("bank", "Virement bancaire"), ("mobile_money", "Mobile Money")],
        string="Moyen de paiement", default="bank", required=True,
    )
    cash_account_id = fields.Many2one("seyal.cash.account", string="Caisse")
    bank_account_id = fields.Many2one("seyal.bank.account", string="Compte bancaire")
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
        ("reference_unique", "unique(reference)", "La reference du paiement doit etre unique."),
        ("amount_positive", "CHECK(amount > 0)", "Le montant doit etre strictement positif."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.constrains("amount", "bill_id", "state")
    def _check_amount_not_exceeding_due(self):
        # Same fix as seyal.payment (Phase 5) : compares against the OTHER
        # confirmed payments' total, never against bill_id.amount_due
        # directly, since amount_due already reflects this payment's own
        # state by the time this runs on a payment being confirmed.
        for rec in self:
            if rec.state == "cancelled":
                continue
            if rec.bill_id.state != "validated":
                raise ValidationError("Impossible d'enregistrer un paiement sur une facture non validee.")
            other_confirmed_amount = sum(self.search([
                ("bill_id", "=", rec.bill_id.id),
                ("state", "=", "confirmed"),
                ("id", "!=", rec.id),
            ]).mapped("amount"))
            if other_confirmed_amount + rec.amount > rec.bill_id.amount_total + 0.001:
                raise ValidationError(
                    "Le total des paiements (%.2f) depasserait le montant de la facture (%.2f)." % (
                        other_confirmed_amount + rec.amount, rec.bill_id.amount_total,
                    )
                )

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un paiement en brouillon peut etre confirme.")
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    "Seul un paiement en brouillon peut etre annule. Un paiement confirme est definitif."
                )
            rec.state = "cancelled"

    def write(self, vals):
        for rec in self:
            if rec.state == "confirmed":
                raise UserError("Un paiement confirme est immuable.")
        return super().write(vals)
