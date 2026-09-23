from odoo import api, fields, models


class SeyalProduct(models.Model):
    _inherit = "seyal.product"

    stock_move_ids = fields.One2many("seyal.stock.move", "product_id", string="Mouvements de stock")
    purchase_line_ids = fields.One2many("seyal.purchase.order.line", "product_id", string="Lignes d'achat")

    qty_on_hand = fields.Float(string="Stock disponible", compute="_compute_qty_on_hand")
    qty_in_transit = fields.Float(string="Stock en transit", compute="_compute_qty_in_transit")

    @api.depends(
        "stock_move_ids.state", "stock_move_ids.qty", "stock_move_ids.move_type",
        "stock_move_ids.dest_warehouse_id", "stock_move_ids.source_warehouse_id",
    )
    def _compute_qty_on_hand(self):
        for rec in self:
            rec.qty_on_hand = self.env["seyal.stock.move"].get_qty_on_hand(rec.id)

    @api.depends(
        "purchase_line_ids.qty", "purchase_line_ids.order_id.is_import", "purchase_line_ids.order_id.state",
        "purchase_line_ids.order_id.import_ids.state",
    )
    def _compute_qty_in_transit(self):
        for rec in self:
            total = 0.0
            for line in rec.purchase_line_ids:
                order = line.order_id
                if order.is_import and order.state == "confirmed":
                    if any(imp.state != "receptionne" for imp in order.import_ids):
                        total += line.qty
            rec.qty_in_transit = total
