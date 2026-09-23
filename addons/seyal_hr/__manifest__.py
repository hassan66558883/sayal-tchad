{
    "name": "SEYAL-TCHAD - Ressources Humaines",
    "version": "17.0.1.0.0",
    "summary": "Employes, departements, presence, conges, avances, salaires pour SEYAL-TCHAD",
    "description": """
RH pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites:
- Departements (seyal.department) et postes (seyal.job.position)
- Employes (seyal.employee), rattaches a une agence/departement/poste
- Presence (seyal.attendance) : pointage entree/sortie, heures travaillees
- Conges/absences (seyal.leave) : demande -> approbation
- Avances sur salaire (seyal.advance) : demande -> approbation
- Bulletins de salaire (seyal.payslip) : salaire de base moins les avances
  approuvees non encore deduites sur la periode - deduction reelle, pas un
  simple affichage du salaire de base

Modeles entierement independants de l'app Odoo native hr (meme decision
qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP STE, qui
utilise deja hr.department via ste_center_accounting).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/seyal_department_views.xml",
        "views/seyal_job_position_views.xml",
        "views/seyal_employee_views.xml",
        "views/seyal_attendance_views.xml",
        "views/seyal_leave_views.xml",
        "views/seyal_advance_views.xml",
        "views/seyal_payslip_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
