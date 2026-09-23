from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalPurchaseOrder(models.Model):
    _name = "seyal.purchase.order"
    _description = "Commande d'achat SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "order_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.purchase.order") or "/",
    )
    supplier_id = fields.Many2one(
        "seyal.partner", string="Fournisseur", required=True, tracking=True,
        domain=[("is_supplier", "=", True)],
    )
    order_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    is_import = fields.Boolean(
        string="Importation", tracking=True,
        help="A cocher si cette commande donne lieu a une importation (conteneur, douane, transit...).",
    )
    state = fields.Selection(
        [
            ("draft", "Proforma"),
            ("confirmed", "Commande"),
            ("done", "Terminee"),
            ("cancelled", "Annulee"),
        ],
        string="Statut", default="draft", required=True, tracking=True,
    )
    line_ids = fields.One2many("seyal.purchase.order.line", "order_id", string="Lignes")
    amount_total = fields.Float(string="Montant total", compute="_compute_amount_total", store=True)

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

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une commande en Proforma peut etre confirmee.")
            if not rec.line_ids:
                raise UserError("Impossible de confirmer une commande sans ligne.")
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
