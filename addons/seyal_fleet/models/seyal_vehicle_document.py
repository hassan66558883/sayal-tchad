from odoo import fields, models


class SeyalVehicleDocument(models.Model):
    _name = "seyal.vehicle.document"
    _description = "Document vehicule SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "expiry_date"

    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule", required=True)
    name = fields.Char(string="Nom", required=True)
    document_type = fields.Selection(
        [
            ("carte_grise", "Carte grise"),
            ("assurance", "Assurance"),
            ("visite_technique", "Visite technique"),
            ("permis_transport", "Permis de transport"),
            ("autre", "Autre"),
        ],
        string="Type", required=True, default="autre",
    )
    file = fields.Binary(string="Fichier")
    filename = fields.Char(string="Nom du fichier")
    expiry_date = fields.Date(string="Date d'expiration")
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )
