from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalPartner(models.Model):
    _name = "seyal.partner"
    _description = "Tiers (client/fournisseur) SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "name"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.partner") or "/",
    )
    name = fields.Char(string="Nom", required=True, tracking=True)

    is_customer = fields.Boolean(string="Client", default=False, tracking=True)
    is_supplier = fields.Boolean(string="Fournisseur", default=False, tracking=True)
    customer_type = fields.Selection(
        [
            ("grossiste", "Grossiste"),
            ("detaillant", "Detaillant"),
            ("supermarche", "Supermarche"),
            ("boutique", "Boutique"),
            ("institution", "Institution"),
        ],
        string="Type de client", tracking=True,
    )

    phone = fields.Char(string="Telephone")
    email = fields.Char(string="Email")
    street = fields.Char(string="Adresse")
    city = fields.Char(string="Ville")
    country_name = fields.Char(string="Pays")

    branch_id = fields.Many2one("seyal.branch", string="Agence de rattachement", tracking=True)
    salesperson_id = fields.Many2one("res.users", string="Commercial responsable", tracking=True)
    credit_limit = fields.Float(string="Limite de credit")

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du tiers doit etre unique."),
    ]

    @api.depends("reference", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.reference}] {rec.name}" if rec.reference and rec.reference != "/" else rec.name

    @api.constrains("is_customer", "is_supplier")
    def _check_customer_or_supplier(self):
        for rec in self:
            if not rec.is_customer and not rec.is_supplier:
                raise ValidationError("Un tiers doit etre au moins client ou fournisseur.")

    @api.constrains("is_customer", "customer_type")
    def _check_customer_type_requires_customer(self):
        for rec in self:
            if rec.customer_type and not rec.is_customer:
                raise ValidationError("Le type de client ne s'applique qu'a un tiers marque 'Client'.")
