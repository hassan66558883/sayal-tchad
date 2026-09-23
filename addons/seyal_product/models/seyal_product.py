from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalProduct(models.Model):
    _name = "seyal.product"
    _description = "Produit SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "name"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.product") or "/",
    )
    name = fields.Char(string="Nom", required=True, tracking=True)
    barcode = fields.Char(string="Code-barres", copy=False)
    category_id = fields.Many2one("seyal.product.category", string="Categorie", tracking=True)
    brand_id = fields.Many2one("seyal.product.brand", string="Marque", tracking=True)

    uom_id = fields.Many2one(
        "seyal.uom", string="Unite de stockage", required=True,
        help="Unite dans laquelle le stock de ce produit est suivi (ex : Kilogramme).",
    )
    uom_po_id = fields.Many2one(
        "seyal.uom", string="Unite de conditionnement",
        help="Unite utilisee a l'achat/vente en gros (ex : Sac de 50 kg). "
             "Doit appartenir a la meme categorie que l'unite de stockage.",
    )

    purchase_price = fields.Float(string="Prix d'achat")
    cost_price = fields.Float(
        string="Prix de revient",
        help="Cout reel : prix d'achat + transport + douane + transit + autres frais "
             "(calcule automatiquement par le module Importations a partir de la Phase 3).",
    )
    sale_price = fields.Float(string="Prix de vente")
    wholesale_price = fields.Float(string="Prix grossiste")
    retail_price = fields.Float(string="Prix detaillant")

    min_stock_qty = fields.Float(string="Stock minimum")
    tracking = fields.Selection(
        [("none", "Aucun"), ("lot", "Par lot")], string="Suivi", default="none",
        help="Indique si ce produit doit etre suivi par lot en stock (mouvements de "
             "stock geres par le module Stocks/Entrepots, Phase 4).",
    )

    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du produit doit etre unique."),
        ("barcode_unique", "unique(barcode)", "Le code-barres doit etre unique."),
    ]

    @api.depends("reference", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.reference}] {rec.name}" if rec.reference and rec.reference != "/" else rec.name

    @api.onchange("uom_id")
    def _onchange_uom_id(self):
        if self.uom_id and not self.uom_po_id:
            self.uom_po_id = self.uom_id

    @api.constrains("uom_id", "uom_po_id")
    def _check_uom_same_category(self):
        for rec in self:
            if rec.uom_po_id and rec.uom_id and rec.uom_po_id.category_id != rec.uom_id.category_id:
                raise ValidationError(
                    "L'unite de conditionnement doit appartenir a la meme categorie "
                    "d'unites que l'unite de stockage."
                )
