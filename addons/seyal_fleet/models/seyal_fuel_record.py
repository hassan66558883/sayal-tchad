from odoo import api, fields, models


class SeyalFuelRecord(models.Model):
    _name = "seyal.fuel.record"
    _description = "Plein de carburant SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "record_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.fuel.record") or "/",
    )
    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule", required=True)
    driver_id = fields.Many2one("seyal.driver", string="Chauffeur")
    record_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    odometer_km = fields.Float(string="Kilometrage", required=True)
    qty_liters = fields.Float(string="Quantite (litres)", required=True)
    unit_price = fields.Float(string="Prix unitaire (par litre)", required=True)
    amount = fields.Float(string="Montant", compute="_compute_amount", store=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du plein doit etre unique."),
        ("qty_positive", "CHECK(qty_liters > 0)", "La quantite doit etre strictement positive."),
        ("odometer_non_negative", "CHECK(odometer_km >= 0)", "Le kilometrage ne peut pas etre negatif."),
    ]

    @api.depends("qty_liters", "unit_price")
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.qty_liters * rec.unit_price
