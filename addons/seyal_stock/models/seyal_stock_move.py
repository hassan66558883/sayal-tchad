from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalStockMove(models.Model):
    _name = "seyal.stock.move"
    _description = "Mouvement de stock SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "move_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.stock.move") or "/",
    )
    move_date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)
    product_id = fields.Many2one("seyal.product", string="Produit", required=True, tracking=True)
    lot_id = fields.Many2one("seyal.stock.lot", string="Lot")
    qty = fields.Float(string="Quantite", required=True)
    move_type = fields.Selection(
        [
            ("in", "Entree"),
            ("out", "Sortie"),
            ("transfer", "Transfert"),
            ("adjustment_in", "Ajustement positif"),
            ("adjustment_out", "Ajustement negatif"),
        ],
        string="Type", required=True, tracking=True,
    )
    source_warehouse_id = fields.Many2one("seyal.warehouse", string="Entrepot source")
    dest_warehouse_id = fields.Many2one("seyal.warehouse", string="Entrepot destination")
    origin_import_id = fields.Many2one("seyal.import", string="Importation d'origine")
    reason = fields.Char(string="Motif")
    state = fields.Selection(
        [("draft", "Brouillon"), ("done", "Valide"), ("cancelled", "Annule")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference du mouvement doit etre unique."),
        ("qty_positive", "CHECK(qty > 0)", "La quantite doit etre strictement positive."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.constrains("move_type", "source_warehouse_id", "dest_warehouse_id")
    def _check_warehouses(self):
        for rec in self:
            if rec.move_type in ("in", "adjustment_in"):
                if not rec.dest_warehouse_id or rec.source_warehouse_id:
                    raise ValidationError(
                        "Une entree/ajustement positif necessite un entrepot destination "
                        "et aucun entrepot source."
                    )
            elif rec.move_type in ("out", "adjustment_out"):
                if not rec.source_warehouse_id or rec.dest_warehouse_id:
                    raise ValidationError(
                        "Une sortie/ajustement negatif necessite un entrepot source "
                        "et aucun entrepot destination."
                    )
            elif rec.move_type == "transfer":
                if not rec.source_warehouse_id or not rec.dest_warehouse_id:
                    raise ValidationError(
                        "Un transfert necessite un entrepot source et un entrepot destination."
                    )
                if rec.source_warehouse_id == rec.dest_warehouse_id:
                    raise ValidationError("Un transfert doit se faire entre deux entrepots differents.")

    def action_validate(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seul un mouvement en brouillon peut etre valide.")
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    "Seul un mouvement en brouillon peut etre annule. Un mouvement valide "
                    "est definitif (creer un mouvement compensatoire si besoin)."
                )
            rec.state = "cancelled"

    def write(self, vals):
        editable_once_done = {"reason"}
        for rec in self:
            if rec.state == "done" and not set(vals.keys()) <= editable_once_done:
                raise UserError("Un mouvement valide est immuable (garantit un historique complet).")
        return super().write(vals)

    @api.model
    def get_qty_on_hand(self, product_id, warehouse_id=None, lot_id=None):
        """Quantite en stock (mouvements valides uniquement).

        Sans `warehouse_id` : stock total toutes agences confondues (un
        transfert entre deux entrepots est neutre au niveau global).
        Avec `warehouse_id` : stock disponible dans cet entrepot precis.
        """
        domain = [("product_id", "=", product_id), ("state", "=", "done")]
        if lot_id:
            domain.append(("lot_id", "=", lot_id))
        moves = self.search(domain)
        qty = 0.0
        for move in moves:
            if warehouse_id:
                if move.dest_warehouse_id.id == warehouse_id and move.move_type in (
                    "in", "adjustment_in", "transfer",
                ):
                    qty += move.qty
                if move.source_warehouse_id.id == warehouse_id and move.move_type in (
                    "out", "adjustment_out", "transfer",
                ):
                    qty -= move.qty
            else:
                if move.move_type in ("in", "adjustment_in"):
                    qty += move.qty
                elif move.move_type in ("out", "adjustment_out"):
                    qty -= move.qty
                # "transfer" is net-zero company-wide : both legs cancel out.
        return qty
