{
    "name": "SEYAL-TCHAD - Rapports",
    "version": "17.0.1.0.0",
    "summary": "Rapports PDF et Excel pour SEYAL-TCHAD",
    "description": """
Rapports pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Un seul assistant generique (seyal.report.export.wizard), pas un ecran par
rapport : le cahier des charges demande des rapports PDF/Excel pour ventes,
achats, stock, importations, clients, fournisseurs, creances, dettes,
marge/benefice, commerciaux, livraisons, vehicules, carburant, depenses,
caisse et banque - 16 types, tous servis par le meme moteur (un type =
une methode de requete + le meme gabarit PDF generique + le meme export
Excel generique), a l'image de ste_reporting sur l'ERP STE ("un seul
composant piloté par les donnees, pas dix ecrans dupliques").

Chaque rapport interroge les vraies donnees construites dans les phases
precedentes (aucune donnee inventee) :
- Marge/benefice : calculee ligne de facture par ligne de facture
  (prix de vente - prix de revient courant du produit), pas une estimation.
- Commerciaux : commissions validees (Phase 9).
- Creances/dettes : seyal.partner.balance/payable_balance (Phases 5 et 7).

Export PDF via le mecanisme QWeb/wkhtmltopdf standard d'Odoo (deja utilise
par l'ERP STE pour ses factures/recus - infrastructure du framework, pas
une app metier partagee). Export Excel via xlsxwriter (deja utilise par
ste_reporting dans ce meme depot).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": [
        "base", "mail", "seyal_base", "seyal_security", "seyal_product", "seyal_partner",
        "seyal_purchase", "seyal_stock", "seyal_sale", "seyal_delivery", "seyal_fleet",
        "seyal_finance", "seyal_commercial",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/seyal_report_generic.xml",
        "views/seyal_report_export_wizard_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
