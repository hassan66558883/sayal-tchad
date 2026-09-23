{
    "name": "SEYAL-TCHAD - Achats et Importations",
    "version": "17.0.1.0.0",
    "summary": "Commandes d'achat, importations et conteneurs pour SEYAL-TCHAD",
    "description": """
Achats et importations pour TECHNOVA ERP - SEYAL-TCHAD (distribution et
importation).

Fonctionnalites:
- Commandes d'achat (seyal.purchase.order) : Proforma -> Commande -> Terminee,
  lignes produits, fournisseur, agence
- Importations (seyal.import) : workflow Fournisseur -> Proforma -> Commande
  -> Expedition -> Conteneur -> Arrivee -> Douane -> Receptionne, BL, ports,
  frais de transport/douane/transit/autres
- Conteneurs (seyal.container) : rattaches a une importation, type, plomb,
  statut
- Calcul automatique du COUT REEL (prix d'achat + transport + douane +
  transit + autres frais), ventile au prorata sur le prix de revient
  (seyal.product.cost_price) de chaque produit lors de la reception

Modeles entierement independants des apps Odoo natives purchase/stock
(meme decision qu'en Phase 2 : isolation totale vis-a-vis de l'ERP STE).

Permissions par agence (Phase 12) : le role "Responsable d'agence" est
restreint aux commandes d'achat de ses agences assignees. Le role Achats
garde l'acces deja accorde ici (Phase 3).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_product", "seyal_partner"],
    "data": [
        "security/ir.model.access.csv",
        "security/seyal_branch_rules.xml",
        "data/ir_sequence_data.xml",
        "views/seyal_purchase_order_views.xml",
        "views/seyal_container_views.xml",
        "views/seyal_import_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
