from odoo import fields, models


class SeyalPurchaseOrder(models.Model):
    _inherit = "seyal.purchase.order"

    import_ids = fields.One2many("seyal.import", "purchase_order_id", string="Importations")
