from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalStockInventory(models.Model):
    _name = "seyal.stock.inventory"
    _description = "Inventaire SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.stock.inventory") or "/",
    )
    warehouse_id = fields.Many2one("seyal.warehouse", string="Entrepot", required=True, tracking=True)
    inventory_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [("draft", "Brouillon"), ("done", "Valide")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    line_ids = fields.One2many("seyal.stock.inventory.line", "inventory_id", string="Lignes")

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de l'inventaire doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    def action_validate(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un inventaire en brouillon peut etre valide.")
            if not rec.line_ids:
                raise UserError("Impossible de valider un inventaire sans ligne.")
            for line in rec.line_ids:
                if line.difference:
                    is_positive = line.difference > 0
                    self.env["seyal.stock.move"].create({
                        "product_id": line.product_id.id,
                        "lot_id": line.lot_id.id if line.lot_id else False,
                        "qty": abs(line.difference),
                        "move_type": "adjustment_in" if is_positive else "adjustment_out",
                        "dest_warehouse_id": rec.warehouse_id.id if is_positive else False,
                        "source_warehouse_id": False if is_positive else rec.warehouse_id.id,
                        "reason": "Ajustement d'inventaire %s" % rec.reference,
                        "state": "done",
                    })
            rec.state = "done"


class SeyalStockInventoryLine(models.Model):
    _name = "seyal.stock.inventory.line"
    _description = "Ligne d'inventaire SEYAL-TCHAD"
    _order = "id"

    inventory_id = fields.Many2one("seyal.stock.inventory", string="Inventaire", required=True, ondelete="cascade")
    product_id = fields.Many2one("seyal.product", string="Produit", required=True)
    lot_id = fields.Many2one("seyal.stock.lot", string="Lot")
    system_qty = fields.Float(string="Quantite theorique", compute="_compute_system_qty", store=True)
    counted_qty = fields.Float(string="Quantite comptee", required=True)
    difference = fields.Float(string="Ecart", compute="_compute_difference", store=True)

    @api.depends("product_id", "inventory_id.warehouse_id")
    def _compute_system_qty(self):
        for rec in self:
            if rec.product_id and rec.inventory_id.warehouse_id:
                rec.system_qty = self.env["seyal.stock.move"].get_qty_on_hand(
                    rec.product_id.id, rec.inventory_id.warehouse_id.id,
                )
            else:
                rec.system_qty = 0.0

    @api.depends("counted_qty", "system_qty")
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.counted_qty - rec.system_qty
