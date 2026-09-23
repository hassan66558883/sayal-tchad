from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalDelivery(models.Model):
    _name = "seyal.delivery"
    _description = "Livraison SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.delivery") or "/",
    )
    route_id = fields.Many2one("seyal.delivery.route", string="Tournee")
    sale_order_id = fields.Many2one(
        "seyal.sale.order", string="Commande", required=True, tracking=True,
        domain=[("state", "in", ("confirmed", "done"))],
    )
    customer_id = fields.Many2one(related="sale_order_id.customer_id", string="Client", store=True)
    line_ids = fields.One2many("seyal.delivery.line", "delivery_id", string="Lignes")
    state = fields.Selection(
        [
            ("planifiee", "Planifiee"),
            ("chargee", "Chargee"),
            ("en_livraison", "En livraison"),
            ("livree", "Livree"),
            ("partielle", "Partielle"),
            ("probleme", "Probleme"),
            ("cloturee", "Cloturee"),
        ],
        string="Statut", default="planifiee", required=True, tracking=True,
    )
    delivery_datetime = fields.Datetime(string="Heure de livraison", readonly=True)
    signature = fields.Binary(string="Signature")
    photo = fields.Binary(string="Photo")
    gps_latitude = fields.Float(string="Latitude GPS", digits=(10, 6))
    gps_longitude = fields.Float(string="Longitude GPS", digits=(10, 6))
    issue_description = fields.Text(string="Probleme signale")

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la livraison doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    "product_id": line.product_id.id,
                    "ordered_qty": line.qty,
                    "delivered_qty": line.qty,
                })
                for line in self.sale_order_id.line_ids
            ]

    @api.model_create_multi
    def create(self, vals_list):
        # The onchange above only fires in a UI form. Populate lines here too
        # so a delivery created directly (API, automation, tests) gets the
        # same lines without requiring the caller to copy them by hand.
        for vals in vals_list:
            if vals.get("sale_order_id") and not vals.get("line_ids"):
                order = self.env["seyal.sale.order"].browse(vals["sale_order_id"])
                vals["line_ids"] = [
                    (0, 0, {
                        "product_id": line.product_id.id,
                        "ordered_qty": line.qty,
                        "delivered_qty": line.qty,
                    })
                    for line in order.line_ids
                ]
        return super().create(vals_list)

    def action_confirm_delivery(self):
        for rec in self:
            if rec.state not in ("chargee", "en_livraison"):
                raise UserError("Seule une livraison chargee ou en cours peut etre confirmee.")
            if not rec.line_ids:
                raise UserError("Impossible de confirmer une livraison sans ligne.")
            if not rec.signature:
                raise UserError("La signature du client est obligatoire pour confirmer la livraison.")
            fully_delivered = all(line.delivered_qty >= line.ordered_qty for line in rec.line_ids)
            any_delivered = any(line.delivered_qty > 0 for line in rec.line_ids)
            rec.state = "livree" if fully_delivered else ("partielle" if any_delivered else "probleme")
            rec.delivery_datetime = fields.Datetime.now()
            rec._create_stock_out_moves()

    def action_report_issue(self):
        for rec in self:
            if rec.state in ("livree", "partielle", "cloturee"):
                raise UserError("Impossible de signaler un probleme sur une livraison deja finalisee.")
            if not rec.issue_description:
                raise UserError("Veuillez decrire le probleme avant de le signaler.")
            rec.state = "probleme"
            rec.delivery_datetime = fields.Datetime.now()

    def _create_stock_out_moves(self):
        # Silently skipped if the route has no warehouse set yet (same
        # graceful-bridge choice as seyal_stock's reception wizard in Phase
        # 4) : the confirmation/signature/photo workflow must stay usable
        # even before warehouse logistics are fully configured.
        for rec in self:
            warehouse = rec.route_id.warehouse_id
            if not warehouse:
                continue
            for line in rec.line_ids.filtered(lambda l: l.delivered_qty > 0):
                self.env["seyal.stock.move"].create({
                    "product_id": line.product_id.id,
                    "qty": line.delivered_qty,
                    "move_type": "out",
                    "source_warehouse_id": warehouse.id,
                    "state": "done",
                    "reason": "Livraison %s" % rec.reference,
                })
