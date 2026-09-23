from odoo import api, fields, models


class SeyalAuditLog(models.Model):
    _name = "seyal.audit.log"
    _description = "Journal d'audit SEYAL-TCHAD"
    _order = "create_date desc"

    user_id = fields.Many2one("res.users", string="Utilisateur", required=True, readonly=True)
    action = fields.Selection([
        ("create", "Creation"),
        ("write", "Modification"),
        ("unlink", "Suppression"),
    ], string="Action", required=True, readonly=True)
    model_name = fields.Char(string="Modele", required=True, readonly=True)
    res_id = fields.Integer(string="ID enregistrement", required=True, readonly=True)
    record_name = fields.Char(string="Enregistrement", readonly=True)
    description = fields.Text(string="Detail", readonly=True)

    @api.model
    def log(self, action, records, description=None):
        """Enregistre une entree d'audit pour chaque enregistrement de `records`.

        Appele par seyal.audit.mixin (create/write/unlink) ; ecrit en sudo()
        pour que le journal ne depende pas des droits de l'utilisateur sur
        seyal.audit.log lui-meme.
        """
        for rec in records:
            self.sudo().create({
                "user_id": self.env.uid,
                "action": action,
                "model_name": records._name,
                "res_id": rec.id,
                "record_name": rec.display_name if action != "unlink" else str(rec.id),
                "description": description,
            })


class SeyalAuditMixin(models.AbstractModel):
    _name = "seyal.audit.mixin"
    _description = "Melange de journalisation d'audit SEYAL-TCHAD"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env["seyal.audit.log"].log("create", records)
        return records

    def write(self, vals):
        result = super().write(vals)
        self.env["seyal.audit.log"].log("write", self, description=str(vals))
        return result

    def unlink(self):
        self.env["seyal.audit.log"].log("unlink", self)
        return super().unlink()
