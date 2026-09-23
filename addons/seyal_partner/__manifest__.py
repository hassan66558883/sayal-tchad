{
    "name": "SEYAL-TCHAD - Clients et fournisseurs",
    "version": "17.0.1.0.0",
    "summary": "Clients et fournisseurs pour SEYAL-TCHAD",
    "description": """
Gestion des clients et fournisseurs pour TECHNOVA ERP - SEYAL-TCHAD
(distribution et importation).

Fonctionnalites:
- Fiche tiers unifiee (seyal.partner) : un meme tiers peut etre client et/ou
  fournisseur (is_customer / is_supplier)
- Types de clients : grossiste, detaillant, supermarche, boutique, institution
- Limite de credit, agence de rattachement, commercial responsable
- Historique via le chatter Odoo standard (mail.thread)

Modele entierement independant de res.partner (decision explicite :
isolation totale vis-a-vis de l'ERP STE, qui utilise deja res.partner dans
cette meme instance Odoo - aucun heritage, aucune dependance fonctionnelle
sur les apps Contacts/Ventes/Achats natives).

Le solde comptable ("solde") n'est pas encore expose : il necessite de
vraies factures/paiements (Phases Ventes et Finance) - non ajoute ici pour
eviter un champ toujours a zero (pas de donnee de substitution).

Permissions par agence (Phase 12) : le role "Responsable d'agence" est
restreint aux tiers de ses agences assignees (branch_id +
res.users.seyal_branch_ids). Les roles Ventes/Achats gardent l'acces large
deja accorde ici (Phase 2), aucune regression pour eux.
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security"],
    "data": [
        "security/ir.model.access.csv",
        "security/seyal_branch_rules.xml",
        "data/ir_sequence_data.xml",
        "views/seyal_partner_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
