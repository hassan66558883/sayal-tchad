from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    seyal_warehouse_ids = fields.Many2many(
        "seyal.warehouse", string="Entrepots geres",
        help="Entrepots auxquels cet utilisateur est rattache. Utilise par les regles "
             "d'acces par entrepot (ir.rule) du role 'Stock / Entrepot' : laisser vide "
             "revient a n'avoir acces aux donnees d'aucun entrepot pour ce role.",
    )
