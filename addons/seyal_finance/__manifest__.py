{
    "name": "SEYAL-TCHAD - Finance",
    "version": "17.0.1.0.0",
    "summary": "Caisse, banque, dettes fournisseurs et depenses pour SEYAL-TCHAD",
    "description": """
Finance pour TECHNOVA ERP - SEYAL-TCHAD (distribution et importation).

Fonctionnalites:
- Caisses (seyal.cash.account) et comptes bancaires (seyal.bank.account) par
  agence, solde calcule en temps reel a partir des mouvements reels
- Factures fournisseurs / dettes (seyal.supplier.bill) : le cote "dettes
  fournisseurs" qui manquait depuis la Phase 3 (les achats/importations
  n'avaient encore aucun suivi de ce que SEYAL-TCHAD doit reellement payer)
- Paiements fournisseurs / decaissements (seyal.supplier.payment) :
  partiels, plafonnes au reste a payer, immuables une fois confirmes (meme
  garde-fou que seyal.payment, Phase 5)
- Depenses (seyal.expense) : loyer, salaires, electricite, carburant,
  entretien, autres - imputees sur une caisse ou un compte bancaire
- Transferts caisse <-> banque (seyal.cash.transfer) : depots et retraits
- seyal.payment (Phase 5) etendu avec caisse/banque de destination
  (facultatif, pour ne pas casser les paiements deja crees sans cette
  information)
- seyal.partner (Phase 2) etendu avec payable_balance : le solde du cote
  dettes fournisseurs, symetrique au balance (creances) de la Phase 5

Modeles entierement independants de l'app Odoo native account (meme
decision qu'aux phases precedentes : isolation totale vis-a-vis de l'ERP
STE).
""",
    "author": "TECHNOTCHAD",
    "category": "Operations/Distribution",
    "depends": ["base", "mail", "seyal_base", "seyal_security", "seyal_partner", "seyal_purchase", "seyal_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/seyal_cash_account_views.xml",
        "views/seyal_bank_account_views.xml",
        "views/seyal_cash_transfer_views.xml",
        "views/seyal_supplier_bill_views.xml",
        "views/seyal_supplier_payment_views.xml",
        "views/seyal_expense_views.xml",
        "views/seyal_payment_views.xml",
        "views/seyal_partner_views.xml",
        "views/seyal_menu.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
