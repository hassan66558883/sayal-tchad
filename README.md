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
| 3 - Achats, importations, conteneurs | A faire | |
| 4 - Stocks, entrepots, mouvements | A faire | |
| 5 - Ventes, facturation | A faire | |
| 6 - Distribution, livraisons, tournees | A faire | |
| 7 - Finance, caisse, banque, creances/dettes | A faire | |
| 8 - Vehicules, carburant | A faire | |
| 9 - Commercial, commissions | A faire | |
| 10 - RH, rapports | A faire | |
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
