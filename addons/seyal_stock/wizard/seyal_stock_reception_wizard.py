from odoo import fields, models
from odoo.exceptions import UserError


class SeyalStockReceptionWizard(models.TransientModel):
    _name = "seyal.stock.reception.wizard"
    _description = "Assistant de reception en stock SEYAL-TCHAD"

    import_id = fields.Many2one("seyal.import", string="Importation", required=True)
    warehouse_id = fields.Many2one("seyal.warehouse", string="Entrepot de destination", required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.import_id.state != "receptionne":
            raise UserError(
                "L'importation doit etre au statut 'Receptionne' avant de generer les entrees de stock."
            )
        moves = self.env["seyal.stock.move"]
        for line in self.import_id.purchase_order_id.line_ids:
            moves |= self.env["seyal.stock.move"].create({
                "product_id": line.product_id.id,
                "qty": line.qty,
                "move_type": "in",
                "dest_warehouse_id": self.warehouse_id.id,
                "origin_import_id": self.import_id.id,
                "state": "draft",
            })
        return {
            "type": "ir.actions.act_window",
            "res_model": "seyal.stock.move",
            "view_mode": "tree,form",
            "domain": [("id", "in", moves.ids)],
            "name": "Entrees de stock generees",
        }
