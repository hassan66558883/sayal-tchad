{
    "name": "SEYAL-TCHAD - Socle",
    "version": "17.0.1.0.0",
    "summary": "Agences et donnees de base pour TECHNOVA ERP - SEYAL-TCHAD",
    "description": """
Module socle de TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites:
- Societe SEYAL-TCHAD (res.company)
- Gestion des agences commerciales (seyal.branch)
- Menu racine "SEYAL-TCHAD" utilise par tous les autres modules metier

Ce module ne depend d'aucun autre module SEYAL : tous les modules metier
(produits, achats, importations, stocks, ventes, distribution, finance,
RH, etc.) dependent de celui-ci pour rattacher leurs donnees a une agence.

Ce module cohabite avec les modules ste_* existants (ERP de la Societe
Tchadienne des Eaux) sans les modifier : deux societes (res.company)
distinctes dans la meme instance Odoo.
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/res_company_data.xml",
        "views/seyal_branch_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
