from odoo import fields, models


class SeyalDriver(models.Model):
    _name = "seyal.driver"
    _description = "Chauffeur SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    license_number = fields.Char(string="Numero de permis")
    phone = fields.Char(string="Telephone")
    user_id = fields.Many2one(
        "res.users", string="Utilisateur lie", copy=False,
        help="Compte utilisateur permettant a ce chauffeur de consulter ses propres tournees/livraisons.",
    )
    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule habituel")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("user_unique", "unique(user_id)", "Cet utilisateur est deja lie a un autre chauffeur."),
    ]
