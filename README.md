# TECHNOVA ERP - SEYAL-TCHAD

ERP pour **SEYAL-TCHAD**, societe de distribution et d'importation, base sur
**Odoo 17 + PostgreSQL**. Editeur/integrateur : **TECHNOTCHAD** ("Smart
Solutions. Real Transformation").

Ce depot est l'espace de developpement standalone de ce projet. Le code a
ete initialement developpe dans un environnement Odoo partage avec un autre
ERP (prefixe de modules `ste_*`, non repris ici) ; le prefixe `seyal_*` sur
chaque module reflete cet historique mais n'a plus d'ambiguite a resoudre
dans ce depot : tous les modules presents ici appartiennent a SEYAL-TCHAD.

## Regles du projet

1. Ne jamais casser une fonctionnalite existante.
2. Ne jamais modifier la base de donnees sans migration.
3. Chaque module doit avoir des tests automatises.
4. Chaque API doit etre documentee.
5. Chaque operation importante doit etre journalisee (voir
   `seyal_security`/`seyal.audit.log`).
6. Ne jamais stocker de mots de passe ou de cles API dans le code source.
7. Modeles SEYAL-TCHAD entierement independants des apps Odoo natives
   (`product`, `stock`, `purchase`, `sale`, `account`, `contacts`) : aucun
   `_inherit` ni dependance fonctionnelle sur elles, y compris pour les
   fonctions qu'elles couvriraient normalement (produits, unites de mesure,
   stock, achats, ventes, facturation) - prefixe `seyal.` partout
   (`seyal.product`, `seyal.partner`, etc.). Seules les references neutres
   sont legitimes : `res.users` (annuaire des utilisateurs), `res.company`
   (`seyal_company`), `mail.thread`/`mail.activity.mixin` (chatter/activites
   standard Odoo).
8. Committer avec Git apres chaque etape stable.
9. Ne pas passer au module suivant tant que le module courant ne passe pas
   ses tests.

## Etat d'avancement

### Phase 1 - Architecture, authentification, roles, socle

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_base`](addons/seyal_base) | Teste (CI) | Societe `SEYAL-TCHAD` (`res.company`), agences commerciales (`seyal.branch`), menu racine "SEYAL-TCHAD" |
| [`seyal_security`](addons/seyal_security) | Teste (CI) | 10 roles metier (Direction generale, Achats, Ventes, Stock/Entrepot, Logistique/Distribution, Chauffeur, Comptable/Finance, Caissier, RH, Responsable d'agence), restriction par agence (`res.users.seyal_branch_ids` + `ir.rule`), MFA disponible (depend de `auth_totp`, standard Odoo), journal d'audit generique (`seyal.audit.log` + melange `seyal.audit.mixin` heritee par ~35 modeles metier pour tracer create/write/unlink automatiquement), historique des connexions (`res.users.log`, lecture seule, reserve Administration/Direction generale) |

### Phase 2 - Produits, categories, marques, unites, fournisseurs, clients

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_product`](addons/seyal_product) | Teste (CI) | Produits (`seyal.product`, reference auto, code-barres, categorie, marque, unite de stockage/conditionnement, prix d'achat/de revient/de vente/grossiste/detaillant, stock minimum), categories hierarchiques (`seyal.product.category`), marques (`seyal.product.brand`), unites de mesure avec conversion (`seyal.uom.category`/`seyal.uom`, ex. demo "1 Sac de 50 kg = 50 KG") |
| [`seyal_partner`](addons/seyal_partner) | Teste (CI) | Tiers unifie client/fournisseur (`seyal.partner`) : types de clients (grossiste, detaillant, supermarche, boutique, institution), limite de credit, agence de rattachement, commercial responsable, historique via chatter, ecrans "Clients"/"Fournisseurs" separes (memes donnees, domaines differents), restriction par agence (Phase 12) |

### Phase 3 - Achats, importations, conteneurs

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_purchase`](addons/seyal_purchase) | Teste (CI) | Commandes d'achat (`seyal.purchase.order`, workflow Proforma -> Commande -> Terminee, lignes produits), importations (`seyal.import`, workflow Fournisseur -> Proforma -> Commande -> Expedition -> Conteneur -> Arrivee -> Douane -> Receptionne, BL, ports, frais transport/douane/transit/autres), conteneurs (`seyal.container`), calcul automatique du COUT REEL (prix d'achat + frais annexes) ventile au prorata sur `seyal.product.cost_price` de chaque produit a la reception, restriction par agence (Phase 12) |

### Phase 4 - Stocks, entrepots, mouvements

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_stock`](addons/seyal_stock) | Teste (CI) | Entrepots/depots (`seyal.warehouse`), lots (`seyal.stock.lot`), mouvements de stock (`seyal.stock.move` : entree/sortie/transfert/ajustement, brouillon -> valide -> immuable), inventaires (`seyal.stock.inventory`, ecart calcule contre le stock theorique, ajustements generes automatiquement a la validation), stock disponible et stock en transit exposes sur la fiche produit (`qty_on_hand`/`qty_in_transit`), assistant de reception (`seyal.stock.reception.wizard`) qui relie une importation receptionnee a de vraies entrees de stock, restriction par entrepot (Phase 12) |

### Phase 5 - Ventes, facturation

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_sale`](addons/seyal_sale) | Teste (CI) | Devis/commandes (`seyal.sale.order`, Devis -> Commande -> Terminee, remise par ligne, controle de la limite de credit a la confirmation), factures et avoirs (`seyal.invoice`, generees depuis une commande confirmee, les avoirs couvrent les retours), paiements clients (`seyal.payment`, partiels, plafonnes au reste a payer, immuables une fois confirmes), solde client reel (`seyal.partner.balance`), restriction par agence (Phase 12) |

### Phase 6 - Distribution, livraisons, tournees

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_delivery`](addons/seyal_delivery) | Teste (CI) | Tournees (`seyal.delivery.route`, Planifiee -> Chargee -> En livraison -> Livree -> Cloturee), livraisons (`seyal.delivery`, rattachees a une commande confirmee, lignes commande/livre pour gerer les livraisons partielles), preuve de livraison (confirmation, signature, photo, heure, GPS facultatif, signalement de probleme), vehicules et chauffeurs, restriction par role (un chauffeur ne voit que ses propres tournees/livraisons), menu "Mes livraisons", confirmation d'une livraison genere un mouvement de stock reel depuis l'entrepot de chargement de la tournee |

### Phase 7 - Finance, caisse, banque, creances/dettes

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_finance`](addons/seyal_finance) | Teste (CI) | Caisses (`seyal.cash.account`) et comptes bancaires (`seyal.bank.account`), solde calcule en temps reel ; factures fournisseurs / dettes (`seyal.supplier.bill`) ; paiements fournisseurs / decaissements (`seyal.supplier.payment`, partiels, plafonnes, immuables) ; depenses (`seyal.expense`, par categorie, imputees sur une caisse ou un compte) ; transferts caisse <-> banque (`seyal.cash.transfer`, depots/retraits, bloques si solde insuffisant) ; `seyal.partner.payable_balance`, symetrique au `balance` (creances) |

### Phase 8 - Vehicules, carburant

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_fleet`](addons/seyal_fleet) | Teste (CI) | Etend `seyal.vehicle`/`seyal.driver` avec pleins de carburant (`seyal.fuel.record`), entretien (`seyal.vehicle.maintenance`), assurance (`seyal.vehicle.insurance`), documents (`seyal.vehicle.document`) ; calcul automatique par vehicule du kilometrage parcouru, de la consommation moyenne (L/100km) et du cout au kilometre a partir des pleins reellement enregistres (methode plein-a-plein sur le kilometrage) |

### Phase 9 - Commercial, commissions

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_commercial`](addons/seyal_commercial) | Teste (CI) | Menu "Mon portefeuille" (filtre de confort sur `seyal.partner.salesperson_id`) ; objectifs commerciaux (`seyal.sales.target`, taux de realisation recalcule a la demande a partir des vraies commandes confirmees) ; baremes de commission (`seyal.commission.rule`, par commercial ou regle par defaut) ; commissions (`seyal.commission`) calculees sur les encaissements reels (paiements confirmes) plutot que sur le simple montant facture |

### Phase 10 - RH, rapports

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_hr`](addons/seyal_hr) | Teste (CI) | Departements (`seyal.department`), postes (`seyal.job.position`), employes (`seyal.employee`), presence (`seyal.attendance`, heures travaillees calculees), conges/absences (`seyal.leave`, demande -> approbation), avances sur salaire (`seyal.advance`, demande -> approbation), bulletins de salaire (`seyal.payslip`, la validation rattache et deduit reellement les avances approuvees non encore deduites sur la periode) |
| [`seyal_reporting`](addons/seyal_reporting) | Teste (CI) | Un seul assistant generique (`seyal.report.export.wizard`) couvrant 16 rapports (ventes, achats, stock, importations, clients, fournisseurs, creances, dettes, marge/benefice, commerciaux, livraisons, vehicules, carburant, depenses, caisse, banque) ; export PDF via QWeb/wkhtmltopdf et export Excel via `xlsxwriter` ; la marge est calculee ligne de facture par ligne de facture (prix de vente - prix de revient courant) |

### Phase 11 - Tableau de bord Direction

| Module | Statut | Description |
| --- | --- | --- |
| [`seyal_dashboard`](addons/seyal_dashboard) | Teste (CI) | Composant client OWL (`seyal.dashboard`) affichant CA du jour/mensuel, ventes, achats, marge, benefice, valeur du stock, ruptures, creances, dettes, importations en cours, livraisons en cours, depenses et encaissements du mois, plus un graphique interactif Chart.js (CA/encaissements par jour, 7/30/90 jours). Accessible a tous les roles via un repli `sudo()` par modele pour ceux sans acces direct, sans jamais elargir leurs droits reels sur les ecrans natifs |

### Phase 12 - Securite, audit, backup, optimisation

Complete `seyal_security`, `seyal_stock`, `seyal_partner`, `seyal_sale` et
`seyal_purchase` avec les points suivants du cahier des charges :

| Point du cahier des charges | Statut |
| --- | --- |
| Authentification securisee | Native Odoo (hachage des mots de passe, limitation des tentatives) |
| MFA | Disponible pour tout utilisateur (`auth_totp`, active individuellement dans les preferences) |
| RBAC / permissions | 10 roles metier + acces par modele sur chaque module |
| Permissions par agence | `seyal.branch`, `seyal.partner`, `seyal.sale.order` et `seyal.purchase.order` (`ir.rule` sur `branch_id` + `res.users.seyal_branch_ids`) pour le role Responsable d'agence |
| Permissions par entrepot | `res.users.seyal_warehouse_ids` + `ir.rule` restreignent le role Stock/Entrepot a ses entrepots assignes sur `seyal.warehouse`/`seyal.stock.move`/`seyal.stock.inventory` |
| Audit logs | `seyal.audit.log`/`seyal.audit.mixin`, applique a ~35 modeles metier |
| Historique des connexions | Ecran en lecture seule sur le modele natif `res.users.log`, reserve a l'administrateur et a la Direction generale |
| Sessions securisees | Native Odoo (cookies de session signes) |
| Validation serveur | `_sql_constraints`/`@api.constrains` sur pratiquement tous les modeles |
| Protection API | Native Odoo (XML-RPC/JSON-RPC respectent les memes `ir.model.access`/`ir.rule` que l'interface web) |
| Protection injection SQL | Par construction : aucune requete SQL brute dans `addons/seyal_*`, uniquement l'ORM Odoo (domaines parametres) |
| Protection XSS | Par construction : aucun `t-raw` dans les templates QWeb, uniquement `t-esc` (echappement automatique) |
| Protection CSRF | Native Odoo (jeton CSRF QWeb sur les formulaires) |
| Backup et restore | `scripts/backup_postgres.sh`/`backup_filestore.sh`/`restore_postgres.sh` a la racine du depot, generiques (`<db_name>` en parametre) |
| Separation des roles (defense en profondeur) | Verifiee par test automatise (`seyal_dashboard`) : un role sans acces direct a un modele (ex. Chauffeur sur `seyal.invoice`) ne peut ni le lire directement, ni le voir via des donnees agregees exposees a tous - decouvert et corrige via ce meme test (voir "Verification" ci-dessous) |

## Verification

L'installation complete des 14 modules et l'execution de leurs suites de
tests sont verifiees par CI (`.github/workflows/tests.yml`), a chaque push,
sur une base PostgreSQL dediee (`ci_test_seyal`).

Etat actuel : **247 tests, 0 echec, 0 erreur**, sur les 14 modules, dans
l'ordre de dependance complet (base -> securite -> produit -> tiers ->
achats -> stock -> ventes -> livraison -> finance -> flotte -> commercial ->
RH -> reporting -> dashboard).

Plusieurs bugs reels ont ete decouverts et corriges via ces executions CI
(code jamais installe/execute auparavant dans l'environnement de
developpement d'origine, faute de daemon Docker disponible) :

- Ordre de chargement du manifest `seyal_security` (groupes de securite
  references avant leur propre definition).
- Extension par melange (`_inherit` en liste) sans `_name` explicite,
  invalide pour Odoo.
- Champs calcules non stockes utilises dans un domaine de vue ou de
  recherche Python (`payment_state`, `balance`, `payable_balance`) -
  "Unsearchable field".
- Selecteur XPath sur un attribut traduisible (`@string`) dans une vue
  heritee - interdit par Odoo (varie selon la langue).
- Etat de livraison jamais synchronise avec l'etat de sa tournee
  (`seyal.delivery` restait bloque en `planifiee`, sans issue possible vers
  `chargee`/`en_livraison`).
- Deux fuites d'acces au principe de separation des roles (`base.group_user`
  accordant un acces en lecture large sur `seyal.invoice`/`seyal.expense` a
  tous les employes, quel que soit leur role) - detectees par le seul test
  du projet qui exerce reellement les ACL avec un utilisateur non
  superutilisateur.
- Verification ACL Odoo sur chaque modele traverse par un domaine de
  recherche (pas seulement le modele interroge) - impactait le calcul de
  marge du tableau de bord pour un role sans acces direct aux factures.

## Deploiement

- **Developpement** : `docker compose up -d` (voir `docker-compose.yml`,
  `odoo.conf`).
- **Production (HTTPS)** : `docker compose -f docker-compose.yml -f
  docker-compose.prod.yml up -d` (voir `docker-compose.prod.yml`,
  `odoo.prod.conf`, `nginx/templates/default.conf.template`). Necessite un
  certificat Let's Encrypt existant avant le premier demarrage de nginx
  (bootstrap via `certbot certonly --standalone`), le nom de domaine
  (`DOMAIN`) et le mot de passe maitre (`ODOO_ADMIN_PASSWORD`) definis dans
  `.env` (copier `.env.example`), et `db_filter` renseigne dans
  `odoo.prod.conf` avant la mise en production.
- **Sauvegarde/restauration** : `scripts/backup_postgres.sh`,
  `scripts/backup_filestore.sh`, `scripts/restore_postgres.sh`.

## A faire avant une mise en production reelle

Hors perimetre de ce depot de developpement : verification manuelle du
rendu visuel des composants OWL (`seyal_dashboard`) dans un navigateur,
parametrage des donnees reelles de l'entreprise (agences, entrepots,
caisses, comptes bancaires, bareme tarifaire, utilisateurs et leurs
roles/agences/entrepots), et `db_filter` en production des qu'il y a plus
d'une base sur le meme serveur PostgreSQL.
