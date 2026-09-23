from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SeyalExpense(models.Model):
    _name = "seyal.expense"
    _description = "Depense SEYAL-TCHAD"
    _inherit = ["mail.thread", "mail.activity.mixin", "seyal.audit.mixin"]
    _order = "expense_date desc, id desc"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("seyal.expense") or "/",
    )
    category = fields.Selection(
        [
            ("loyer", "Loyer"),
            ("salaires", "Salaires"),
            ("electricite", "Electricite"),
            ("eau", "Eau"),
            ("carburant", "Carburant"),
            ("entretien", "Entretien"),
            ("fournitures", "Fournitures"),
            ("autre", "Autre"),
        ],
        string="Categorie", required=True, default="autre", tracking=True,
    )
    branch_id = fields.Many2one("seyal.branch", string="Agence")
    expense_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Float(string="Montant", required=True)
    description = fields.Text(string="Description")
    cash_account_id = fields.Many2one("seyal.cash.account", string="Caisse")
    bank_account_id = fields.Many2one("seyal.bank.account", string="Compte bancaire")
    state = fields.Selection(
        [("draft", "Brouillon"), ("confirmed", "Confirmee"), ("cancelled", "Annulee")],
        string="Statut", default="draft", required=True, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Societe", required=True,
        default=lambda self: self.env.ref("seyal_base.seyal_company", raise_if_not_found=False)
        or self.env.company,
    )

    _sql_constraints = [
        ("reference_unique", "unique(reference)", "La reference de la depense doit etre unique."),
        ("amount_positive", "CHECK(amount > 0)", "Le montant doit etre strictement positif."),
    ]

    @api.depends("reference")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.reference or str(rec.id)

    @api.constrains("cash_account_id", "bank_account_id")
    def _check_single_account(self):
        for rec in self:
            if rec.cash_account_id and rec.bank_account_id:
                raise ValidationError("Une depense ne peut etre imputee qu'a une seule caisse OU un seul compte.")

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Seule une depense en brouillon peut etre confirmee.")
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    "Seule une depense en brouillon peut etre annulee. Une depense confirmee est definitive."
                )
            rec.state = "cancelled"

    def write(self, vals):
        for rec in self:
            if rec.state == "confirmed":
                raise UserError("Une depense confirmee est immuable.")
        return super().write(vals)
