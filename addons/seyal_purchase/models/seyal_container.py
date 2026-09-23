from odoo import fields, models


class SeyalContainer(models.Model):
    _name = "seyal.container"
    _description = "Conteneur SEYAL-TCHAD"
    _order = "number"

    number = fields.Char(string="Numero de conteneur", required=True)
    import_id = fields.Many2one("seyal.import", string="Importation", required=True, ondelete="cascade")
    container_type = fields.Selection(
        [("20", "20 pieds"), ("40", "40 pieds"), ("40hc", "40 pieds High Cube")],
        string="Type", default="20",
    )
    seal_number = fields.Char(string="Numero de plomb")
    status = fields.Selection(
        [
            ("in_transit", "En transit"),
            ("arrived", "Arrive au port"),
            ("customs", "En douane"),
            ("released", "Libere"),
        ],
        string="Statut", default="in_transit",
    )
    arrival_date = fields.Date(string="Date d'arrivee")

    _sql_constraints = [
        ("number_unique", "unique(number)", "Le numero de conteneur doit etre unique."),
    ]
