from odoo import models


class SeyalBranch(models.Model):
    _name = "seyal.branch"
    _inherit = ["seyal.branch", "seyal.audit.mixin"]
