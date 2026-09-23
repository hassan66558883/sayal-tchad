from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalDeliveryRoute(models.Model):
    _name = "seyal.delivery.route"
    _description = "Tournee de livraison SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "route_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.delivery.route") or "/",
    )
    route_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    driver_id = fields.Many2one("seyal.driver", string="Chauffeur", required=True, tracking=True)
    vehicle_id = fields.Many2one("seyal.vehicle", string="Vehicule", required=True, tracking=True)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    warehouse_id = fields.Many2one(
        "seyal.warehouse", string="Entrepot de chargement",
        help="Utilise pour generer les sorties de stock a la confirmation de chaque livraison.",
    )
    state = fields.Selection(
        [
            ("planifiee", "Planifiee"),
            ("chargee", "Chargee"),
            ("en_livraison", "En livraison"),
            ("livree", "Livree"),
            ("cloturee", "Cloturee"),
        ],
        string="Statut", default="planifiee", required=True, tracking=True,
    )
    delivery_ids = fields.One2many("seyal.delivery", "route_id", string="Livraisons")

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la tournee doit etre unique."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    def action_charger(self):
        for rec in self:
            if rec.state != "planifiee":
                raise UserError("Seule une tournee planifiee peut etre chargee.")
            if not rec.delivery_ids:
                raise UserError("Impossible de charger une tournee sans livraison.")
            rec.state = "chargee"
            rec.delivery_ids.filtered(lambda d: d.state == "planifiee").write({"state": "chargee"})

    def action_demarrer(self):
        for rec in self:
            if rec.state != "chargee":
                raise UserError("Seule une tournee chargee peut demarrer.")
            rec.state = "en_livraison"
            rec.delivery_ids.filtered(lambda d: d.state == "chargee").write({"state": "en_livraison"})

    def action_terminer(self):
        for rec in self:
            if rec.state != "en_livraison":
                raise UserError("Seule une tournee en livraison peut etre terminee.")
            unfinished = rec.delivery_ids.filtered(lambda d: d.state not in ("livree", "partielle", "probleme"))
            if unfinished:
                raise UserError("Toutes les livraisons doivent etre traitees avant de terminer la tournee.")
            rec.state = "livree"

    def action_cloturer(self):
        for rec in self:
            if rec.state != "livree":
                raise UserError("Seule une tournee livree peut etre cloturee.")
            rec.state = "cloturee"
