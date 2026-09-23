from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalPayment(models.Model):
    _name = "seyal.payment"
    _description = "Paiement client SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "payment_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.payment") or "/",
    )
    invoice_id = fields.Many2one("seyal.invoice", string="Facture", required=True, tracking=True)
    customer_id = fields.Many2one(related="invoice_id.customer_id", string="Client", store=True)
    payment_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Float(string="Montant", required=True)
    method = fields.Selection(
        [("cash", "Especes"), ("bank", "Virement bancaire"), ("mobile_money", "Mobile Money")],
        string="Moyen de paiement", default="cash", required=True,
    )
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

    @api.constrains("amount", "invoice_id", "state")
    def _check_amount_not_exceeding_due(self):
        # Compares against the OTHER confirmed payments' total, never against
        # invoice_id.amount_due directly: by the time this runs on a payment
        # being confirmed, its own state='confirmed' is already applied, so
        # amount_due would already have subtracted this same payment - using
        # it here would make a payment wrongly fail against its own amount.
        for rec in self:
            if rec.state == "cancelled":
                continue
            if rec.invoice_id.state != "validated":
                raise ValidationError("Impossible d'enregistrer un paiement sur une facture non validee.")
            other_confirmed_amount = sum(self.search([
                ("invoice_id", "=", rec.invoice_id.id),
                ("state", "=", "confirmed"),
                ("id", "!=", rec.id),
            ]).mapped("amount"))
            if other_confirmed_amount + rec.amount > rec.invoice_id.amount_total + 0.001:
                raise ValidationError(
                    "Le total des paiements (%.2f) depasserait le montant de la facture (%.2f)." % (
                        other_confirmed_amount + rec.amount, rec.invoice_id.amount_total,
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
