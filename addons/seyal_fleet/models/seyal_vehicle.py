from odoo import api, fields, models


class SeyalVehicle(models.Model):
    _inherit = "seyal.vehicle"

    fuel_record_ids = fields.One2many("seyal.fuel.record", "vehicle_id", string="Pleins de carburant")
    maintenance_ids = fields.One2many("seyal.vehicle.maintenance", "vehicle_id", string="Entretiens")
    insurance_ids = fields.One2many("seyal.vehicle.insurance", "vehicle_id", string="Assurances")
    document_ids = fields.One2many("seyal.vehicle.document", "vehicle_id", string="Documents")

    total_fuel_liters = fields.Float(string="Total carburant (litres)", compute="_compute_fuel_stats")
    total_fuel_cost = fields.Float(string="Total cout carburant", compute="_compute_fuel_stats")
    total_km = fields.Float(string="Kilometrage parcouru", compute="_compute_fuel_stats")
    avg_consumption_l_per_100km = fields.Float(
        string="Consommation moyenne (L/100km)", compute="_compute_fuel_stats",
    )
    cost_per_km = fields.Float(string="Cout au kilometre", compute="_compute_fuel_stats")

    @api.depends("fuel_record_ids.qty_liters", "fuel_record_ids.amount", "fuel_record_ids.odometer_km")
    def _compute_fuel_stats(self):
        for rec in self:
            records = rec.fuel_record_ids
            rec.total_fuel_liters = sum(records.mapped("qty_liters"))
            rec.total_fuel_cost = sum(records.mapped("amount"))
            odometers = records.mapped("odometer_km")
            rec.total_km = (max(odometers) - min(odometers)) if len(odometers) >= 2 else 0.0
            if rec.total_km > 0:
                rec.avg_consumption_l_per_100km = (rec.total_fuel_liters / rec.total_km) * 100
                rec.cost_per_km = rec.total_fuel_cost / rec.total_km
            else:
                rec.avg_consumption_l_per_100km = 0.0
                rec.cost_per_km = 0.0
