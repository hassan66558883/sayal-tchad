# TECHNOVA ERP - SEYAL-TCHAD

ERP pour **SEYAL-TCHAD**, societe de distribution et d'importation, editeur
**TECHNOTCHAD** ("Smart Solutions. Real Transformation").

Stack : **FastAPI + SQLAlchemy + Alembic + PostgreSQL** (backend/API) et
**React + TypeScript + Vite** (frontend), sans framework ERP tiers -
chaque fonctionnalite (auth, RBAC, audit, workflow metier) est implementee
directement dans ce depot.

## Regles du projet

1. Ne jamais casser une fonctionnalite existante.
2. Ne jamais modifier le schema de base de donnees sans migration Alembic.
3. Chaque module/route doit avoir des tests automatises (pytest, contre une
   vraie base PostgreSQL - jamais de mock de la base).
4. Chaque API doit etre documentee (FastAPI genere `/docs` automatiquement
   a partir des schemas Pydantic et docstrings).
5. Chaque creation/modification/suppression sur un modele "audite" doit
   etre journalisee automatiquement (voir `backend/app/services/audit.py`).
6. Ne jamais stocker de mots de passe ou de cles API dans le code source
   (variables d'environnement / `.env`, jamais committe).
7. Committer avec Git apres chaque etape stable.
8. Ne pas passer a la phase suivante tant que la phase courante ne passe
   pas ses tests.

## Architecture

```
backend/
  app/
    core/       config, session DB, securite (hash mot de passe, JWT),
                dependances FastAPI (utilisateur courant, controle de role)
    models/     modeles SQLAlchemy (un fichier par entite)
    schemas/    schemas Pydantic (validation entree/sortie API)
    routers/    endpoints FastAPI, un fichier par ressource
    services/   logique metier partagee (audit, RBAC par agence, seed)
  alembic/      migrations de schema
  tests/        pytest, contre une vraie base PostgreSQL locale

frontend/
  src/
    api/        client HTTP (axios) + types + fonctions d'appel par ressource
    auth/       contexte d'authentification (token JWT, utilisateur courant)
    components/ mise en page partagee (sidebar, route protegee)
    pages/      un composant par ecran
```

### Authentification et roles

JWT (Bearer token) obtenu via `POST /api/auth/login` (OAuth2 password
flow). 10 roles metier fixes, seedes au demarrage (`app/services/seed.py`) :
Direction generale, Achats, Ventes, Stock/Entrepot, Logistique/
Distribution, Chauffeur, Comptable/Finance, Caissier, RH, Responsable
d'agence. Chaque route protegee declare les roles autorises via la
dependance `require_roles(...)` (`app/core/deps.py`) ; un superutilisateur
outrepasse tous les controles.

### Restriction par agence

`app/services/rbac.py` : un utilisateur n'ayant QUE le role Responsable
d'agence (pas Direction generale, pas superutilisateur) ne voit que les
enregistrements lies a une agence qui lui est assignee - et ne voit rien
du tout sans assignation (secure-by-default). Reutilisable par toute
future route filtrant par `branch_id`.

### Audit automatique

Tout modele SQLAlchemy heritant de `AuditedMixin`
(`app/models/mixins.py`) est automatiquement journalise (creation/
modification/suppression) via un seul listener SQLAlchemy au niveau de
la session (`app/services/audit.py`), sans qu'aucune route n'ait besoin
d'appeler quoi que ce soit manuellement.

## Etat d'avancement

| Phase | Statut | Description |
| --- | --- | --- |
| 1 - Architecture, auth, roles, agences, audit | **Fait** (24 tests) | Auth JWT, 10 roles metier, agences (`Branch`) avec restriction par agence, journal d'audit automatique, ecrans Agences/Utilisateurs/Journal d'audit |
| 2 - Produits, categories, marques, unites, tiers | **Fait** (38 tests) | Produits (reference auto PRD######, categories, marques, unite de stockage), categories/unites de mesure avec conversion (`app/services/uom.py`), tiers unifie client/fournisseur (reference TRS######, types de client, restriction par agence pour le role Responsable d'agence), ecrans Produits/Clients \& Fournisseurs |
| 3 - Achats, importations, conteneurs | **Fait** (57 tests) | Commandes d'achat (reference auto ACH######, workflow Proforma -> Commande -> Terminee/Annulee, lignes produits avec contrainte serveur qty>0), conteneurs, importations (reference IMP######, workflow Nouveau -> Expedie -> Arrive -> Douane -> Receptionne, une seule importation par commande) ; calcul du COUT REEL (montant de la commande + frais transport/douane/transit/autres) ventile au prorata sur `Product.cost_price` a la reception (`app/services/import_cost.py`), ecrans Commandes d'achat/Importations |
| 4 - Stocks, entrepots, mouvements | **Fait** (77 tests) | Entrepots, lots (`StockLot`), mouvements de stock (entree/sortie/transfert/ajustement, brouillon -> valide -> immuable sauf le motif, `app/services/stock.py` pour le calcul du stock disponible/en transit a partir des vraies relations), inventaires (ecart calcule contre le stock theorique reel, ajustements generes automatiquement a la validation), pont importation -> stock (`app/services/reception.py`, cree les entrees de stock en brouillon a partir d'une importation receptionnee), stock disponible et en transit exposes via `GET /api/products/{id}/stock`, ecrans Entrepots/Mouvements de stock/Inventaires |
| 5 - Ventes, facturation | **Fait** (99 tests) | Devis/commandes (reference auto CMD######, workflow Devis -> Commande -> Terminee/Annulee, remise par ligne, controle de la limite de credit du client a la confirmation - 0 = illimite), factures et avoirs (reference FAC######, generees depuis une commande confirmee, les avoirs couvrent les retours et reduisent directement le solde client), paiements clients (partiels, plafonnes au reste a payer calcule en temps reel - jamais un champ mis en cache - contre la somme des AUTRES paiements confirmes, evitant par construction le bug d'auto-comptage corrige a posteriori dans la version Odoo precedente de ce projet), solde client reel via `GET /api/partners/{id}/balance`, ecrans Devis \& commandes/Factures |
| 6 - Distribution, livraisons, tournees | **Fait** (110 tests) | Vehicules et chauffeurs (chauffeur optionnellement lie a un compte utilisateur), tournees (reference auto TRN######, workflow Planifiee -> Chargee -> En livraison -> Livree -> Cloturee - charger/demarrer une tournee cascade automatiquement le meme changement d'etat sur toutes ses livraisons, corrigeant des le depart le bug de sequencement route/livraison decouvert a posteriori dans la version Odoo precedente de ce projet), livraisons (reference auto LIV######, une par commande confirmee, lignes commande/livree pour gerer les livraisons partielles avec contrainte serveur livree<=commandee), preuve de livraison (signature ou signalement de probleme obligatoire pour confirmer, photo, horodatage, GPS facultatif), confirmation d'une livraison genere un vrai mouvement de stock de sortie (deja valide) depuis l'entrepot de chargement de la tournee, pour la quantite reellement livree uniquement ; restriction par role pour le chauffeur (`app/services/driver_scope.py`, ne voit que ses propres tournees/livraisons via le compte utilisateur lie a sa fiche, rien du tout sans liaison), ecran "Mes livraisons" avec confirmation directe, ecrans Vehicules \& chauffeurs/Tournees |
| 7 - Finance, caisse, banque, creances/dettes | **Fait** (122 tests) | Factures fournisseurs / dettes (reference auto FRS######, mirroir cote achat du module Ventes : `bill`/`debit_note`, generees depuis une commande d'achat confirmee, `amount_paid`/`amount_due`/`payment_state` toujours calcules en temps reel, jamais mis en cache), paiements fournisseurs (plafonnes au reste a payer via une somme live des AUTRES paiements confirmes, meme protection anti-auto-comptage que cote client), solde fournisseur reel via `GET /api/partners/{id}/supplier-balance` ; caisses et sessions de caisse (ouverture/cloture avec fonds de depart, solde reel toujours recalcule en direct a partir des paiements/depenses rattaches - jamais stocke - et compare au montant physiquement compte a la cloture pour un ecart, meme logique que l'inventaire de stock de la Phase 4) ; comptes bancaires (solde calcule a partir du solde initial, des paiements/depenses rattaches et des mouvements manuels) et mouvements bancaires manuels ; depenses (reference auto DEP######, brouillon -> validee, categorie et mode de paiement especes/banque) ; paiements clients (Phase 5) et paiements/depenses peuvent desormais etre rattaches a une session de caisse ou un compte bancaire (facultatif, retro-compatible) pour alimenter leur solde reel ; ecrans Dettes fournisseurs/Caisse/Banque, solde fournisseur ajoute a l'ecran Clients \& Fournisseurs |
| 8 - Vehicules, carburant | **Fait** (131 tests) | Pleins de carburant (litres x prix unitaire calcule en temps reel, jamais stocke), entretiens vehicule (planifie -> termine/annule, cout compte uniquement une fois termine), documents vehicule (assurance/controle technique/vignette, date de debut/fin avec contrainte serveur fin>=debut, endpoint dedie pour les documents expirant sous N jours et banniere d'alerte sur l'ecran) ; pleins et entretiens payes en especes/banque peuvent etre rattaches a une session de caisse ou un compte bancaire (obligatoire des que le cout est superieur a 0, contrairement aux paiements clients/fournisseurs qui restent facultatifs) et alimentent desormais leur solde reel au meme titre que les depenses (`app/services/finance.py` etendu en consequence - un vrai bug detecte par le test navigateur de bout en bout, pas seulement par les tests unitaires, puis corrige avant ce commit), cout total carburant/entretien par vehicule via `GET /api/vehicles/{id}/fuel-cost` et `/maintenance-cost`, ecran Carburant \& entretien |
| 9 - Commercial, commissions | **Fait** (139 tests) | Commerciaux (optionnellement lies a un compte utilisateur, taux de commission 0-100%), commande de vente desormais rattachable a un commercial (colonne facultative et retro-compatible sur `sale_orders`) ; commission et chiffre d'affaires realise toujours calcules en temps reel a partir des commandes reellement confirmees/terminees sur la periode demandee (jamais stockes), en excluant explicitement les devis non confirmes et les commandes annulees ; objectifs commerciaux par periode avec pourcentage d'atteinte calcule en direct (meme principe que l'ecart de caisse de la Phase 7 et l'inventaire de stock de la Phase 4), ecran Commercial |
| 10 - RH, rapports | **Fait** (147 tests) | Employes (optionnellement lies a un compte utilisateur, comme Chauffeur/Commercial), demandes de conge (en_attente -> approuvee/refusee, contrainte serveur fin>=debut ; un employe lie a son propre compte peut soumettre et ne voir que ses propres demandes - meme restriction "Mes X" que le chauffeur de la Phase 6, `app/services/hr_scope.py`), bulletins de paie (reference auto BUL######, brouillon -> valide, `net_pay` = salaire de base + primes - retenues toujours calcule en direct, jamais stocke) ; un bulletin valide en especes/banque exige desormais une session de caisse/un compte bancaire (comme le carburant et l'entretien de la Phase 8) et alimente le meme solde reel (`app/services/finance.py` etendu une troisieme fois, cette fois sans regression grace au reflexe pris en Phase 8) ; rapports Ventes (commandes confirmees/facture net des avoirs/encaisse) et RH (effectif actif, en conge aujourd'hui, cout de la masse salariale), tout calcule en temps reel sur la periode demandee, ecrans Ressources humaines/Rapports |
| 11 - Tableau de bord Direction | A faire | |
| 12 - Securite, audit, backup, optimisation | A faire | |

## Developpement local

Necessite PostgreSQL (local ou via `docker compose up -d db`), Python
3.11+, Node 20+.

```bash
# Base de donnees
docker compose up -d db
# ou un PostgreSQL local existant : creer un role + deux bases
#   createuser seyal --pwprompt
#   createdb seyal_dev -O seyal
#   createdb seyal_test -O seyal

# Backend
cd backend
cp .env.example .env   # renseigner DATABASE_URL, JWT_SECRET_KEY, etc.
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload

# Frontend (autre terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173, proxy /api -> http://localhost:8000
```

### Premier compte administrateur

Aucun utilisateur n'existe a la creation de la base : definir
`ADMIN_BOOTSTRAP_EMAIL`/`ADMIN_BOOTSTRAP_PASSWORD` dans `backend/.env`
avant le premier demarrage cree automatiquement un superutilisateur (une
seule fois, tant qu'aucun superutilisateur n'existe deja). A retirer du
`.env` une fois ce premier compte cree.

### Tests

```bash
cd backend
export DATABASE_URL=postgresql+psycopg://seyal:<mot de passe>@localhost:5432/seyal_test
python -m pytest -v
```

La CI (`.github/workflows/tests.yml`) execute ces memes tests contre un
service PostgreSQL ephemere a chaque push, plus la verification
TypeScript/lint du frontend.
