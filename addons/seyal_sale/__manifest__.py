{
    "name": "SEYAL-TCHAD - Ventes et Facturation",
    "version": "17.0.1.0.0",
    "summary": "Devis, commandes, factures, avoirs et paiements pour SEYAL-TCHAD",
    "description": """
Ventes et facturation pour TECHNOVA ERP - SEYAL-TCHAD (distribution et
importation).

Fonctionnalites:
- Devis/commandes (seyal.sale.order) : Devis -> Commande -> Terminee, lignes
  avec remise par ligne, prix par defaut selon le type de client (grossiste/
  detaillant), controle de la limite de credit client a la confirmation
- Factures et avoirs (seyal.invoice, move_type facture/avoir - les avoirs
  couvrent les retours), generees depuis une commande confirmee
- Paiements clients (seyal.payment) : partiels, plusieurs paiements par
  facture, plafonnes au reste a payer, immuables une fois confirmes
- Solde client (seyal.partner.balance) desormais reel : somme des factures
  validees non soldees moins les avoirs - la promesse laissee en Phase 2
  ("pas de placeholder") est tenue ici, une fois les factures/paiements
  reellement construits

Modeles entierement independants des apps Odoo natives sale/account (meme
decision qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP
STE). La preparation/livraison physique de la commande releve du module
Distribution (Phase 6), pas de celui-ci.

Permissions par agence (Phase 12) : le role "Responsable d'agence" est
restreint aux commandes de vente de ses agences assignees. Les roles
Ventes/Comptable gardent l'acces deja accorde ici (Phase 5).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_product", "seyal_partner"],
    "data": [
        "security/ir.model.access.csv",
        "security/seyal_branch_rules.xml",
        "data/ir_sequence_data.xml",
        "views/seyal_sale_order_views.xml",
        "views/seyal_invoice_views.xml",
        "views/seyal_payment_views.xml",
        "views/seyal_partner_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
