{
    "name": "SEYAL-TCHAD - Produits",
    "version": "17.0.1.0.0",
    "summary": "Produits, categories, marques et unites de mesure pour SEYAL-TCHAD",
    "description": """
Gestion des produits pour TECHNOVA ERP - SEYAL-TCHAD (distribution et
importation).

Fonctionnalites:
- Produits (seyal.product) : reference auto-generee, code-barres, categorie,
  marque, unite de stockage et unite de conditionnement, prix d'achat, prix
  de revient, prix de vente, prix grossiste, prix detaillant, stock minimum
- Categories de produits (seyal.product.category), hierarchiques
- Marques (seyal.product.brand)
- Unites de mesure et conversions (seyal.uom.category / seyal.uom), avec
  gestion des conditionnements (ex : 1 sac = 50 KG)

Modeles entierement independants des apps Odoo natives product/stock
(decision explicite : isolation totale vis-a-vis de l'ERP STE, qui utilise
deja product.template/stock via ste_meter_stock dans cette meme instance
Odoo - aucun heritage, aucune dependance fonctionnelle sur ces apps).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/seyal_uom_data.xml",
        "views/seyal_product_category_views.xml",
        "views/seyal_product_brand_views.xml",
        "views/seyal_uom_views.xml",
        "views/seyal_product_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
