{
    "name": "SEYAL-TCHAD - Stocks et Entrepots",
    "version": "17.0.1.0.0",
    "summary": "Entrepots, lots, mouvements et inventaires pour SEYAL-TCHAD",
    "description": """
Stocks et entrepots pour TECHNOVA ERP - SEYAL-TCHAD (distribution et
importation).

Fonctionnalites:
- Entrepots/depots (seyal.warehouse), rattaches a une agence
- Lots (seyal.stock.lot)
- Mouvements de stock (seyal.stock.move) : entrees, sorties, transferts,
  ajustements ; brouillon -> valide (immuable une fois valide, garantit un
  historique complet) -> annule
- Inventaires (seyal.stock.inventory) : comptage physique, ecart calcule
  automatiquement contre le stock theorique, generation automatique des
  mouvements d'ajustement correspondants a la validation
- Stock disponible et stock en transit exposes sur la fiche produit
  (qty_on_hand / qty_in_transit, calcules a partir des mouvements valides et
  des importations non encore receptionnees - Phase 3)
- Assistant de reception (seyal.stock.reception.wizard) : transforme une
  importation receptionnee (Phase 3) en entrees de stock brouillon, a
  valider par un responsable de stock

Modeles entierement independants de l'app Odoo native stock (meme decision
qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP STE).

Stock reserve non expose ici (volontairement, pas de placeholder) : n'a de
sens qu'une fois des commandes de vente reservant du stock (Phase 5).

Permissions par entrepot (Phase 12) : res.users.seyal_warehouse_ids +
ir.rule restreignent le role "Stock / Entrepot" (seyal_security) a ses
entrepots assignes sur seyal.warehouse/seyal.stock.move/
seyal.stock.inventory - meme principe que la restriction par agence
(Phase 1) et par chauffeur (Phase 6).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_product", "seyal_purchase"],
    "data": [
        "security/ir.model.access.csv",
        "security/seyal_warehouse_rules.xml",
        "data/ir_sequence_data.xml",
        "views/seyal_warehouse_views.xml",
        "views/seyal_stock_lot_views.xml",
        "views/seyal_stock_move_views.xml",
        "views/seyal_stock_inventory_views.xml",
        "views/seyal_product_views.xml",
        "views/res_users_views.xml",
        "wizard/seyal_stock_reception_wizard_views.xml",
        "views/seyal_import_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
