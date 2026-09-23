{
    "name": "SEYAL-TCHAD - Vehicules et Carburant",
    "version": "17.0.1.0.0",
    "summary": "Carburant, entretien, assurance et documents vehicules pour SEYAL-TCHAD",
    "description": """
Vehicules pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites (completant seyal.vehicle/seyal.driver crees en Phase 6) :
- Pleins de carburant (seyal.fuel.record) : litres, prix, kilometrage
- Entretien (seyal.vehicle.maintenance) : intervention, cout, kilometrage
- Assurance (seyal.vehicle.insurance) : police, assureur, validite, cout
- Documents (seyal.vehicle.document) : carte grise, assurance, visite
  technique, permis de transport, avec date d'expiration
- Calcul automatique, par vehicule, du kilometrage total, de la
  consommation moyenne (L/100km) et du cout au kilometre a partir des
  pleins de carburant reellement enregistres

Modeles entierement independants de l'app Odoo native fleet (meme decision
qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP STE, qui
utilise deja fleet.vehicle via ste_fleet_mission).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_delivery"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/seyal_fuel_record_views.xml",
        "views/seyal_vehicle_maintenance_views.xml",
        "views/seyal_vehicle_insurance_views.xml",
        "views/seyal_vehicle_document_views.xml",
        "views/seyal_vehicle_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
