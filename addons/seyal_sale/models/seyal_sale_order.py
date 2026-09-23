from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalSaleOrder(models.Model):
    _name = "seyal.sale.order"
    _description = "Commande de vente SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "order_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.sale.order") or "/",
    )
    customer_id = fields.Many2one(
        "seyal.partner", string="Client", required=True, tracking=True,
        domain=[("is_customer", "=", True)],
    )
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    salesperson_id = fields.Many2one("res.users", string="Commercial")
    order_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [
            ("draft", "Devis"),
            ("confirmed", "Commande"),
            ("done", "Terminee"),
            ("cancelled", "Annulee"),
        ],
        string="Statut", default="draft", required=True, tracking=True,
    )
    line_ids = fields.One2many("seyal.sale.order.line", "order_id", string="Lignes")
    amount_total = fields.Float(string="Montant total", compute="_compute_amount_total", store=True)
    invoice_ids = fields.One2many("seyal.invoice", "sale_order_id", string="Factures")

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la commande doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.depends("line_ids.subtotal")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped("subtotal"))

    @api.onchange("customer_id")
    def _onchange_customer_id(self):
        if self.customer_id.salesperson_id:
            self.salesperson_id = self.customer_id.salesperson_id
        if self.customer_id.branch_id:
            self.branch_id = self.customer_id.branch_id

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un devis peut etre confirme en commande.")
            if not rec.line_ids:
                raise UserError("Impossible de confirmer une commande sans ligne.")
            if rec.customer_id.credit_limit > 0:
                projected_balance = rec.customer_id.balance + rec.amount_total
                if projected_balance > rec.customer_id.credit_limit:
                    raise UserError(
                        "Limite de credit depassee pour %s : solde actuel %.2f + commande %.2f "
                        "depasserait la limite de %.2f." % (
                            rec.customer_id.name, rec.customer_id.balance, rec.amount_total,
                            rec.customer_id.credit_limit,
                        )
                    )
            rec.state = "confirmed"

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError("Seule une commande confirmee peut etre marquee terminee.")
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.state == "done":
                raise UserError("Une commande terminee ne peut pas etre annulee.")
            rec.state = "cancelled"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_create_invoice(self):
        self.ensure_one()
        if self.state not in ("confirmed", "done"):
            raise UserError("Seule une commande confirmee peut etre facturee.")
        invoice = self.env["seyal.invoice"].create({
            "customer_id": self.customer_id.id,
            "sale_order_id": self.id,
            "move_type": "invoice",
            "line_ids": [
                (0, 0, {
                    "product_id": line.product_id.id,
                    "qty": line.qty,
                    "unit_price": line.unit_price,
                    "discount_percent": line.discount_percent,
                })
                for line in self.line_ids
            ],
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "seyal.invoice",
            "view_mode": "form",
            "res_id": invoice.id,
        }
