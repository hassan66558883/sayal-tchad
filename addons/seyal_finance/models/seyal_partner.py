from odoo import api, fields, models


class SeyalPartner(models.Model):
    _inherit = "seyal.partner"

    bill_ids = fields.One2many("seyal.supplier.bill", "supplier_id", string="Factures fournisseur")
    payable_balance = fields.Float(
        string="Solde fournisseur (dette)", compute="_compute_payable_balance", store=True,
        help="Somme des factures fournisseur validees non soldees.",
    )

    @api.depends(
        "bill_ids.state", "bill_ids.amount_due", "bill_ids.amount_total",
        "bill_ids.payment_ids.amount", "bill_ids.payment_ids.state",
    )
    def _compute_payable_balance(self):
        for rec in self:
            bills = rec.bill_ids.filtered(lambda b: b.state == "validated")
            rec.payable_balance = sum(bills.mapped("amount_due"))
