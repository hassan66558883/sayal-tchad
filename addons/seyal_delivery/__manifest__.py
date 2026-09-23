{
    "name": "SEYAL-TCHAD - Distribution et Livraisons",
    "version": "17.0.1.0.0",
    "summary": "Tournees, livraisons et preuve de livraison pour SEYAL-TCHAD",
    "description": """
Distribution pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites:
- Tournees de livraison (seyal.delivery.route) : Planifiee -> Chargee ->
  En livraison -> Livree -> Cloturee
- Livraisons (seyal.delivery) : rattachees a une commande de vente confirmee
  (Phase 5), lignes avec quantite commandee/livree (livraison partielle)
- Preuve de livraison : confirmation, signature, photo, heure, position GPS
  (facultative), signalement de probleme - toutes cote chauffeur
- Vehicules (seyal.vehicle) et chauffeurs (seyal.driver) : fiches legeres
  pour l'instant (immatriculation, capacite, permis) - le suivi complet
  (carburant, entretien, assurance, documents) est la Phase 8
- Restriction par role : un chauffeur ne voit que ses propres tournees et
  livraisons (res.users lie a seyal.driver + ir.rule), menu "Mes livraisons"
  dedie
- A la confirmation d'une livraison, generation automatique d'une vraie
  sortie de stock (seyal.stock.move, Phase 4) depuis l'entrepot de
  chargement de la tournee - c'est ici, et non a la simple confirmation
  d'une commande de vente, que le stock diminue reellement

Modeles entierement independants des apps Odoo natives delivery/fleet (meme
decision qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP
STE, qui utilise deja fleet.vehicle via ste_fleet_mission).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": [
        "base", "mail", "seyal_base", "seyal_security", "seyal_product", "seyal_partner",
        "seyal_sale", "seyal_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/seyal_delivery_rules.xml",
        "data/ir_sequence_data.xml",
        "views/seyal_vehicle_views.xml",
        "views/seyal_driver_views.xml",
        "views/seyal_delivery_route_views.xml",
        "views/seyal_delivery_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
