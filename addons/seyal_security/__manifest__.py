{
    "name": "SEYAL-TCHAD - Securite",
    "version": "17.0.1.0.0",
    "summary": "Roles metier, restriction par agence et journal d'audit pour SEYAL-TCHAD",
    "description": """
Securite de TECHNOVA ERP - SEYAL-TCHAD.

Fonctionnalites:
- Roles metier (Direction generale, Achats, Ventes, Stock, Logistique,
  Chauffeur, Comptable, Caissier, RH, Responsable d'agence)
- Restriction des donnees par agence (res.users.seyal_branch_ids + ir.rule),
  meme principe que ste_security/ste_center_ids pour l'autre ERP de cette
  instance
- Authentification a deux facteurs disponible pour tous les utilisateurs
  (module standard Odoo auth_totp, active par utilisateur dans ses
  preferences)
- Journal d'audit generique (seyal.audit.log / seyal.audit.mixin) : les
  modules metier des phases suivantes heriteront de seyal.audit.mixin pour
  tracer automatiquement creations/modifications/suppressions - seyal.branch
  (Phase 1) en herite ici (Phase 12) pour une couverture complete
- Historique des connexions (Phase 12) : ecran en lecture seule sur le
  modele natif res.users.log (un enregistrement par connexion reussie,
  cree nativement par res.users._update_last_login()) - reserve a
  l'administrateur et a la Direction generale
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["seyal_base", "mail", "auth_totp"],
    "data": [
        "security/seyal_security_groups.xml",
        "security/ir.model.access.csv",
        "security/seyal_branch_rules.xml",
        "views/res_users_views.xml",
        "views/seyal_audit_log_views.xml",
        "views/res_users_log_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
