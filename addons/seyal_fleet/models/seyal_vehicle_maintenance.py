from odoo import fields, models


class SeyalVehicleMaintenance(models.Model):
    _name = "seyal.vehicle.maintenance"
    _description = "Entretien vehicule SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "maintenance_date desc, id desc"

    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule", required=True)
    maintenance_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    description = fields.Char(string="Intervention", required=True)
    cost = fields.Float(string="Cout")
    odometer_km = fields.Float(string="Kilometrage")
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )
