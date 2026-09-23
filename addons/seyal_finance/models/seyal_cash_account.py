from odoo import api, fields, models


class SeyalCashAccount(models.Model):
    _name = "seyal.cash.account"
    _description = "Caisse SEYAL-TCHAD"
    _inherit = ["seyal.audit.mixin"]
    _order = "name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True, copy=False)
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    client_payment_ids = fields.One2many("seyal.payment", "cash_account_id", string="Encaissements clients")
    supplier_payment_ids = fields.One2many(
        "seyal.supplier.payment", "cash_account_id", string="Decaissements fournisseurs",
    )
    expense_ids = fields.One2many("seyal.expense", "cash_account_id", string="Depenses")
    transfer_ids = fields.One2many("seyal.cash.transfer", "cash_account_id", string="Transferts")

    balance = fields.Float(string="Solde", compute="_compute_balance")

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code de la caisse doit etre unique."),
    ]

    @api.depends(
        "client_payment_ids.amount", "client_payment_ids.state",
        "supplier_payment_ids.amount", "supplier_payment_ids.state",
        "expense_ids.amount", "expense_ids.state",
        "transfer_ids.amount", "transfer_ids.state", "transfer_ids.direction",
    )
    def _compute_balance(self):
        for rec in self:
            encaisse = sum(rec.client_payment_ids.filtered(lambda p: p.state == "confirmed").mapped("amount"))
            decaisse_fournisseur = sum(
                rec.supplier_payment_ids.filtered(lambda p: p.state == "confirmed").mapped("amount")
            )
            depenses = sum(rec.expense_ids.filtered(lambda e: e.state == "confirmed").mapped("amount"))
            transferts_confirmes = rec.transfer_ids.filtered(lambda t: t.state == "confirmed")
            depots = sum(transferts_confirmes.filtered(lambda t: t.direction == "deposit").mapped("amount"))
            retraits = sum(transferts_confirmes.filtered(lambda t: t.direction == "withdrawal").mapped("amount"))
            rec.balance = encaisse - decaisse_fournisseur - depenses - depots + retraits
