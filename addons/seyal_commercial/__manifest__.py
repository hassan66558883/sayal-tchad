{
    "name": "SEYAL-TCHAD - Commercial et Commissions",
    "version": "17.0.1.0.0",
    "summary": "Portefeuille clients, objectifs et commissions pour SEYAL-TCHAD",
    "description": """
Commercial pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites:
- Portefeuille clients : menu "Mon portefeuille" filtrant les clients dont
  le commercial connecte est responsable (seyal.partner.salesperson_id,
  Phase 2) - filtre de confort, pas une restriction d'acces (le role Ventes
  garde l'acces large deja accorde en Phase 5, aucune regression)
- Objectifs commerciaux (seyal.sales.target) : objectif par commercial et
  periode, taux de realisation calcule sur demande a partir des vraies
  commandes confirmees (seyal.sale.order, Phase 5)
- Baremes de commission (seyal.commission.rule) : taux par commercial ou
  regle par defaut
- Commissions (seyal.commission) : calculees sur les encaissements reels
  (seyal.payment confirmes, Phase 5) des commandes du commercial sur la
  periode - pas sur le simple montant facture, pour ne pas remunerer une
  vente non encore payee par un client a credit

Modeles entierement independants (meme decision qu'aux phases precedentes :
isolation totale vis-a-vis de l'ERP STE).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_partner", "seyal_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/seyal_commission_rule_views.xml",
        "views/seyal_sales_target_views.xml",
        "views/seyal_commission_views.xml",
        "views/seyal_partner_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
