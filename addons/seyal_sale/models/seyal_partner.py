from odoo import api, fields, models


class SeyalPartner(models.Model):
    _inherit = "seyal.partner"

    invoice_ids = fields.One2many("seyal.invoice", "customer_id", string="Factures")
    balance = fields.Float(
        string="Solde", compute="_compute_balance", store=True,
        help="Somme des factures validees non soldees, moins les avoirs valides.",
    )

    @api.depends(
        "invoice_ids.state", "invoice_ids.move_type", "invoice_ids.amount_due",
        "invoice_ids.amount_total", "invoice_ids.payment_ids.amount", "invoice_ids.payment_ids.state",
    )
    def _compute_balance(self):
        for rec in self:
            invoices = rec.invoice_ids.filtered(lambda inv: inv.state == "validated")
            total = 0.0
            for inv in invoices:
                sign = 1 if inv.move_type == "invoice" else -1
                total += sign * inv.amount_due
            rec.balance = total
