from odoo import fields, models


class SeyalPayment(models.Model):
    _inherit = "seyal.payment"

    cash_account_id = fields.Many2one("seyal.cash.account", string="Caisse")
    bank_account_id = fields.Many2one("seyal.bank.account", string="Compte bancaire")
