from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalCommissionRule(models.Model):
    _name = "seyal.commission.rule"
    _description = "Bareme de commission SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "salesperson_id"

    name = fields.Char(string="Nom", required=True)
    salesperson_id = fields.Many2one(
        "res.users", string="Commercial",
        help="Laisser vide pour une regle par defaut, appliquee a tout commercial sans regle specifique.",
    )
    rate_percent = fields.Float(string="Taux (%)", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("rate_range", "CHECK(rate_percent >= 0 AND rate_percent <= 100)",
         "Le taux doit etre compris entre 0 et 100%."),
    ]

    @api.constrains("salesperson_id", "active")
    def _check_unique_active_rule(self):
        for rec in self.filtered("active"):
            domain = [("active", "=", True), ("id", "!=", rec.id)]
            domain.append(("salesperson_id", "=", rec.salesperson_id.id if rec.salesperson_id else False))
            if self.search_count(domain):
                raise ValidationError(
                    "Il existe deja une regle de commission active pour ce commercial "
                    "(ou une regle par defaut)."
                )
