from odoo import api, fields, models
from odoo.exceptions import UserError


class SeyalImport(models.Model):
    _name = "seyal.import"
    _description = "Importation SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.import") or "/",
    )
    purchase_order_id = fields.Many2one(
        "seyal.purchase.order", string="Commande d'achat", required=True, tracking=True,
        domain=[("is_import", "=", True)],
    )
    supplier_id = fields.Many2one(related="purchase_order_id.supplier_id", string="Fournisseur", store=True)

    state = fields.Selection(
        [
            ("nouveau", "Nouveau"),
            ("expedie", "Expedie"),
            ("arrive", "Arrive au port"),
            ("douane", "En douane"),
            ("receptionne", "Receptionne"),
        ],
        string="Statut", default="nouveau", required=True, tracking=True,
    )

    bl_number = fields.Char(string="Numero de BL")
    port_of_loading = fields.Char(string="Port de chargement")
    port_of_discharge = fields.Char(string="Port de dechargement")
    expedition_date = fields.Date(string="Date d'expedition")
    arrival_date = fields.Date(string="Date d'arrivee")

    transport_cost = fields.Float(string="Frais de transport")
    customs_cost = fields.Float(string="Frais de douane")
    transit_cost = fields.Float(string="Frais de transit")
    other_costs = fields.Float(string="Autres frais")

    purchase_amount = fields.Float(
        string="Montant achat", related="purchase_order_id.amount_total", store=True,
    )
    total_extra_costs = fields.Float(string="Total frais annexes", compute="_compute_total_extra_costs", store=True)
    real_cost = fields.Float(
        string="Cout reel", compute="_compute_real_cost", store=True,
        help="COUT REEL = prix d'achat + transport + douane + transit + autres frais.",
    )

    container_ids = fields.One2many("seyal.container", "import_id", string="Conteneurs")

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de l'importation doit etre unique."),
        ("purchase_order_unique", "unique(purchase_order_id)",
         "Cette commande d'achat a deja une importation associee."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.depends("transport_cost", "customs_cost", "transit_cost", "other_costs")
    def _compute_total_extra_costs(self):
        for rec in self:
            rec.total_extra_costs = rec.transport_cost + rec.customs_cost + rec.transit_cost + rec.other_costs

    @api.depends("purchase_amount", "total_extra_costs")
    def _compute_real_cost(self):
        for rec in self:
            rec.real_cost = rec.purchase_amount + rec.total_extra_costs

    def action_expedier(self):
        for rec in self:
            if rec.state != "nouveau":
                raise UserError("Seule une importation 'Nouveau' peut etre expediee.")
            if rec.purchase_order_id.state != "confirmed":
                raise UserError("La commande d'achat liee doit etre confirmee avant expedition.")
            rec.state = "expedie"

    def action_arrivee(self):
        for rec in self:
            if rec.state != "expedie":
                raise UserError("Seule une importation expediee peut etre marquee arrivee.")
            rec.state = "arrive"

    def action_douane(self):
        for rec in self:
            if rec.state != "arrive":
                raise UserError("Seule une importation arrivee peut passer en douane.")
            rec.state = "douane"

    def action_receptionner(self):
        for rec in self:
            if rec.state != "douane":
                raise UserError("Seule une importation en douane peut etre receptionnee.")
            rec._apply_real_cost_to_products()
            rec.state = "receptionne"
            rec.purchase_order_id.action_done()

    def _apply_real_cost_to_products(self):
        """Ventile le prix d'achat + les frais annexes sur le prix de revient
        (seyal.product.cost_price) de chaque produit de la commande, au
        prorata du sous-total de chaque ligne - implemente la formule du
        cahier des charges : COUT REEL = prix achat + transport + douane +
        transit + autres frais.
        """
        for rec in self:
            lines = rec.purchase_order_id.line_ids
            total_amount = sum(lines.mapped("subtotal"))
            if not total_amount:
                continue
            for line in lines:
                share = line.subtotal / total_amount
                allocated_extra = rec.total_extra_costs * share
                landed_unit_cost = (line.subtotal + allocated_extra) / line.qty
                line.product_id.cost_price = landed_unit_cost
