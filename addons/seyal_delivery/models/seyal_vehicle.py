from odoo import fields, models


class SeyalVehicle(models.Model):
    _name = "seyal.vehicle"
    _description = "Vehicule SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "name"

    name = fields.Char(string="Nom/Modele", required=True)
    plate_number = fields.Char(string="Immatriculation", required=True, copy=False)
    capacity_kg = fields.Float(string="Capacite (kg)")
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("plate_number_unique", "unique(plate_number)", "Cette immatriculation existe deja."),
    ]
