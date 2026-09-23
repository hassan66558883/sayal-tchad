{
    "name": "SEYAL-TCHAD - Tableau de bord Direction",
    "version": "17.0.1.0.0",
    "summary": "Tableau de bord Direction Generale pour SEYAL-TCHAD",
    "description": """
Tableau de bord Direction pour TECHNOVA ERP - SEYAL-TCHAD.

Indicateurs (seyal.dashboard.get_kpis(), toujours calcules en Python a
partir des vrais modeles des phases precedentes, jamais de valeur
inventee) : CA du jour, CA mensuel, ventes, achats, marge, benefice
(marge brute - depenses du mois - simplification honnete, pas une
comptabilite complete), valeur du stock, ruptures de stock, creances,
dettes fournisseurs, importations en cours, livraisons en cours, depenses
du mois, encaissements du mois. Graphique interactif (Chart.js) du CA/
encaissements par jour (7/30/90 jours).

Architecture calquee sur ste_dashboard (ERP STE, meme depot) : composant
client OWL enregistre via registry.category("actions"), chargement du
bundle web.chartjs_lib, methodes RPC decorees @api.model (evite le bug de
dispatch documente dans ste_dashboard - un appel ORM sans ids sur une
methode non @api.model plante avec IndexError cote serveur), et le meme
correctif CSS de defilement (.o_seyal_dashboard { height: 100%; overflow-y:
auto; } - une action client n'est pas enveloppee dans le conteneur
scrollable standard d'Odoo).

Le rendu visuel (JS) ne peut pas etre verifie par la suite de tests Python
dans cet environnement de developpement (pas de navigateur) - a verifier
manuellement, comme deja documente pour ste_dashboard/ste_gis dans ce
depot. La logique d'agregation des indicateurs, elle, est entierement
testee.
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": [
        "base", "web", "seyal_base", "seyal_security", "seyal_product", "seyal_partner",
        "seyal_purchase", "seyal_stock", "seyal_sale", "seyal_delivery", "seyal_finance",
    ],
    "data": [
        "views/seyal_dashboard_actions.xml",
        "views/seyal_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "seyal_dashboard/static/src/js/seyal_dashboard.js",
            "seyal_dashboard/static/src/xml/seyal_dashboard.xml",
            "seyal_dashboard/static/src/css/seyal_dashboard.css",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
