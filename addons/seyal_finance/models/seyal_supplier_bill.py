from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalSupplierBill(models.Model):
    _name = "seyal.supplier.bill"
    _description = "Facture fournisseur SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "bill_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.supplier.bill") or "/",
    )
    purchase_order_id = fields.Many2one("seyal.purchase.order", string="Commande d'origine")
    supplier_id = fields.Many2one(
        "seyal.partner", string="Fournisseur", required=True, tracking=True,
        domain=[("is_supplier", "=", True)],
    )
    bill_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [("draft", "Brouillon"), ("validated", "Validee"), ("cancelled", "Annulee")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    line_ids = fields.One2many("seyal.supplier.bill.line", "bill_id", string="Lignes")
    payment_ids = fields.One2many("seyal.supplier.payment", "bill_id", string="Paiements")
    amount_total = fields.Float(string="Montant total", compute="_compute_amount_total", store=True)
    amount_paid = fields.Float(string="Montant paye", compute="_compute_amount_paid", store=True)
    amount_due = fields.Float(string="Reste a payer", compute="_compute_amount_paid", store=True)
    payment_state = fields.Selection(
        [("not_paid", "Non payee"), ("partially_paid", "Partiellement payee"), ("paid", "Payee")],
        string="Etat du paiement", compute="_compute_amount_paid", store=True,
    )

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la facture fournisseur doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.depends("line_ids.subtotal")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped("subtotal"))

    @api.depends("amount_total", "payment_ids.amount", "payment_ids.state")
    def _compute_amount_paid(self):
        for rec in self:
            paid = sum(rec.payment_ids.filtered(lambda p: p.state == "confirmed").mapped("amount"))
            rec.amount_paid = paid
            rec.amount_due = rec.amount_total - paid
            if rec.amount_total <= 0 or paid <= 0:
                rec.payment_state = "not_paid"
            elif paid >= rec.amount_total:
                rec.payment_state = "paid"
            else:
                rec.payment_state = "partially_paid"

    def action_validate(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une facture fournisseur en brouillon peut etre validee.")
            if not rec.line_ids:
                raise UserError("Impossible de valider une facture fournisseur sans ligne.")
            rec.state = "validated"

    def action_cancel(self):
        for rec in self:
            if rec.state == "validated" and rec.amount_paid:
                raise UserError("Impossible d'annuler une facture deja partiellement ou totalement payee.")
            rec.state = "cancelled"
