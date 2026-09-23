from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SeyalUom(models.Model):
    _name = "seyal.uom"
    _description = "Unite de mesure SEYAL-TCHAD"
    _order = "category_id, factor"

    name = fields.Char(string="Nom", required=True)
    category_id = fields.Many2one("seyal.uom.category", string="Categorie", required=True, ondelete="restrict")
    is_reference = fields.Boolean(
        string="Unite de reference",
        help="L'unite de reference de la categorie a un facteur de 1.0 ; toutes les "
             "autres unites de la categorie sont exprimees en multiples de celle-ci.",
    )
    factor = fields.Float(
        string="Facteur (par rapport a la reference)", required=True, default=1.0,
        help="Exemple : categorie 'Poids', reference 'Kilogramme' (facteur 1.0), "
             "'Sac de 50 kg' (facteur 50.0) -> 1 Sac = 50 KG.",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("factor_positive", "CHECK(factor > 0)", "Le facteur doit etre strictement positif."),
    ]

    @api.constrains("category_id", "is_reference")
    def _check_single_reference_per_category(self):
        for rec in self.filtered("is_reference"):
            others = self.search([
                ("category_id", "=", rec.category_id.id),
                ("is_reference", "=", True),
                ("id", "!=", rec.id),
            ])
            if others:
                raise ValidationError(
                    "La categorie '%s' a deja une unite de reference (%s)." % (
                        rec.category_id.name, others[0].name,
                    )
                )

    def convert_qty(self, qty, to_uom):
        """Convertit `qty` (exprimee dans self) vers l'unite `to_uom` de la meme categorie."""
        self.ensure_one()
        to_uom.ensure_one()
        if self.category_id != to_uom.category_id:
            raise ValidationError("Impossible de convertir entre deux categories d'unites differentes.")
        qty_in_reference = qty * self.factor
        return qty_in_reference / to_uom.factor
