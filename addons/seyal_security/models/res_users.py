from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    seyal_branch_ids = fields.Many2many(
        "seyal.branch", string="Agences gerees",
        help="Agences auxquelles cet utilisateur est rattache. Utilise par les regles "
             "d'acces par agence (ir.rule) du role 'Responsable d'agence' : laisser "
             "vide revient a n'avoir acces aux donnees d'aucune agence pour ce role.",
    )
