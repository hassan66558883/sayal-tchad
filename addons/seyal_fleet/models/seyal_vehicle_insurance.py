from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalVehicleInsurance(models.Model):
    _name = "seyal.vehicle.insurance"
    _description = "Assurance vehicule SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "end_date desc"

    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule", required=True)
    policy_number = fields.Char(string="Numero de police", required=True)
    insurer = fields.Char(string="Assureur")
    start_date = fields.Date(string="Date de debut", required=True)
    end_date = fields.Date(string="Date de fin", required=True)
    cost = fields.Float(string="Cout")
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("La date de fin doit etre posterieure a la date de debut.")
