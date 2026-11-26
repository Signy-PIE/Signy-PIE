# Signy PIE

> Application pédagogique pour apprendre la **langue des signes française (LSF)**, avec reconnaissance des gestes par intelligence artificielle.

Signy PIE s'adresse aux proches de personnes sourdes ou malentendantes qui souhaitent apprendre des signes pour mieux communiquer au quotidien. L'application propose des leçons guidées et un retour automatique sur les gestes réalisés devant la caméra, sans jamais envoyer la vidéo à un serveur.

---

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Flux de données](#flux-de-données)
- [Prérequis](#prérequis)
- [Installation et démarrage](#installation-et-démarrage)
- [Variables d'environnement](#variables-denvironnement)
- [API](#api)
- [Base de données](#base-de-données)
- [Structure du projet](#structure-du-projet)
- [Commandes utiles](#commandes-utiles)
- [Vie privée et données](#vie-privée-et-données)
- [Contribuer](#contribuer)

---

## Architecture

```
Signy PIE
├── frontend/          # Application Vue 3 / TypeScript / Vite
│   ├── src/
│   │   ├── views/     # Pages (leçons, exercice, lexique…)
│   │   ├── components/# Composants réutilisables
│   │   ├── api/       # Clients HTTP vers le backend
│   │   ├── router/    # Vue Router
│   │   └── lib/       # Utilitaires (MediaPipe, helpers…)
│   └── public/
│       └── mediapipe/ # Modèles MediaPipe servis localement
│
└── backend/           # API FastAPI / Python
    ├── routes/        # Endpoints HTTP (ai, lessons, users, words…)
    ├── services/      # Logique métier (prétraitement, prédiction, interrogation)
    ├── schemas/       # Validation Pydantic (requêtes / réponses)
    ├── db/            # Connexion, modèles SQLAlchemy, migrations, seed
    ├── utils/         # Fonctions utilitaires
    └── assets/        # Modèle ONNX et metadata.json
```

### Stack technique

| Couche | Technologie |
|---|---|
| Interface | Vue 3, TypeScript, Vite, Vue Router |
| Analyse du mouvement | MediaPipe Tasks Vision (`@mediapipe/tasks-vision`) |
| Serveur API | FastAPI, Uvicorn, Python 3.12 |
| Validation | Pydantic v2 |
| Reconnaissance IA | ONNX Runtime (`onnxruntime`) |
| Base de données | SQLAlchemy 2 — SQLite (local) ou PostgreSQL (Docker/prod) |
| Conteneurisation | Docker Compose (PostgreSQL 16, pgAdmin 4) |
| Qualité code | ESLint, Prettier, mypy (optionnel) |

---

## Flux de données

```
┌─────────────────────────────────────┐
│            Navigateur               │
│                                     │
│  1. Capture vidéo (caméra locale)   │
│  2. Extraction MediaPipe            │
│     → mains, pose, visage           │
│     (96 points / image)             │
│  3. Prévisualisation à l'utilisateur│
│  4. Validation → envoi des points   │
└───────────────┬─────────────────────┘
                │  POST /ai/interrogate
                │  { points, masques, cadence, mot_attendu }
                ▼
┌─────────────────────────────────────┐
│            Backend FastAPI          │
│                                     │
│  5. Validation Pydantic             │
│  6. Prétraitement NumPy             │
│     → tenseur float32 (1, 90, 350)  │
│  7. Inférence ONNX Runtime          │
│  8. Réponse : { signe, validé }     │
└─────────────────────────────────────┘
```

> **La vidéo ne quitte jamais le navigateur.** Seuls les points de squelette normalisés sont transmis au serveur. Ils ne sont pas persistés en base.

---

## Prérequis

| Outil | Version minimale |
|---|---|
| Node.js | 22.18.0 ou ≥ 24.11.0 |
| Docker & Docker Compose | ≥ 24 |

---

## Installation et démarrage

### Frontend

```sh
cd frontend
npm install
npm run dev
```

L'interface est accessible sur **http://localhost:5173**.

### Backend

Le backend tourne via Docker Compose avec PostgreSQL 16 et pgAdmin 4.

```sh
# Copier et remplir le fichier d'environnement
cp backend/.env.example backend/.env

# Démarrer les services (depuis backend/)
cd backend
docker compose up --build
```

| Service | URL locale |
|---|---|
| Backend API | http://localhost:8000 |
| Documentation Swagger | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

### Accéder aux tables avec pgAdmin

1. Ouvrir **http://localhost:5050** et se connecter avec les identifiants du `.env` (`PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`).
2. Cliquer sur **"Add New Server"**.
3. Onglet **General** → donner un nom (ex. `Signy`).
4. Onglet **Connection** → remplir :

| Champ | Valeur |
|---|---|
| Host name/address | `db` *(nom du service Docker)* |
| Port | `5432` |
| Maintenance database | `signy` |
| Username | valeur de `POSTGRES_USER` |
| Password | valeur de `POSTGRES_PASSWORD` |

5. Cocher **Save password**, puis **Save**.
6. Naviguer dans l'arbre : `Servers → Signy → Databases → signy → Schemas → public → Tables`.
7. Clic droit sur une table → **View/Edit Data → All Rows** pour consulter les données.

> **Remarque :** le host doit être `postgres` (nom du conteneur Docker) et non `localhost`, car pgAdmin tourne lui aussi dans Docker.

Pour peupler la base avec des données de démonstration :

```sh
docker compose exec backend python -m db.seed
```

---

## Variables d'environnement

### Backend — `backend/.env`

| Variable | Obligatoire | Description |
|---|---|---|
| `POSTGRES_DB` | Docker uniquement | Nom de la base PostgreSQL |
| `POSTGRES_USER` | Docker uniquement | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | Docker uniquement | Mot de passe PostgreSQL |
| `PGADMIN_DEFAULT_EMAIL` | Docker uniquement | Email de connexion pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | Docker uniquement | Mot de passe pgAdmin |
| `DATABASE_URL` | Non (SQLite par défaut) | URL de connexion SQLAlchemy complète |

Exemple de `DATABASE_URL` pour PostgreSQL :
```
DATABASE_URL=postgresql+psycopg2://utilisateur:mot_de_passe@localhost:5432/signy
```

### Frontend — `frontend/.env.local`

| Variable | Par défaut | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL de base du backend |

Pour tester sur mobile via un tunnel HTTPS, utiliser le proxy Vite :
```
VITE_API_URL=/api
```

---

## API

### Endpoints principaux

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | Vérification de l'état du service |
| `GET` | `/lessons` | Liste des leçons |
| `GET` | `/lessons/{id}` | Détail d'une leçon et ses mots |
| `GET` | `/words` | Catalogue de mots |
| `GET` | `/users` | Liste des utilisateurs |
| `GET` | `/users/{id}` | Détail d'un utilisateur |
| `POST` | `/ai/interrogate` | Reconnaissance d'un signe à partir de points MediaPipe |

### `POST /ai/interrogate`

Corps de la requête :

```json
{
  "points": [[...], ...],
  "masques": [...],
  "cadence": 30,
  "mot_attendu": "bonjour"
}
```

Réponse :

```json
{
  "signe": "bonjour",
  "valide": true,
  "confiance": 0.97
}
```

**Codes d'erreur :** `422` si les points sont invalides ou le mot inconnu du modèle — `503` si le modèle ONNX est indisponible.

### Contrat du modèle

| Paramètre | Valeur |
|---|---|
| Points par image | 96 |
| Entrée ONNX | `float32 (1, 90, 350)` |
| Prétraitement | `mediapipe96-geometrie175-v1` |
| Nombre de classes | 80 |

---

## Base de données

### Diagramme ERD

```mermaid
erDiagram
    users {
        int id PK
        string nom
        string prenom
        string email
        string password
        boolean premium
        datetime creation_date
    }

    lessons {
        int id PK
        string title
    }

    words {
        int id PK
        string string
    }

    word_corespondance {
        int id PK
        string label
        json words
    }

    user_lessons_done {
        int user_id FK
        int lesson_id FK
    }

    lesson_words {
        int lesson_id FK
        int word_id FK
    }

    word_corespondance_words {
        int corespondance_id FK
        int word_id FK
    }

    users ||--o{ user_lessons_done : "complète"
    lessons ||--o{ user_lessons_done : "complétée par"
    lessons ||--o{ lesson_words : "contient"
    words ||--o{ lesson_words : "appartient à"
    word_corespondance ||--o{ word_corespondance_words : "regroupe"
    words ||--o{ word_corespondance_words : "référencé dans"
```

### Tables

#### `users` — Utilisateurs

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | `integer` | PK, auto-incrémenté | Identifiant unique |
| `nom` | `string` | NOT NULL | Nom de famille |
| `prenom` | `string` | NOT NULL | Prénom |
| `email` | `string` | NOT NULL, UNIQUE, indexé | Adresse e-mail |
| `password` | `string` | NOT NULL | Mot de passe (haché) |
| `premium` | `boolean` | NOT NULL, défaut `false` | Accès premium |
| `creation_date` | `datetime` | NOT NULL, défaut `now()` | Date de création du compte |

#### `lessons` — Leçons

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | `integer` | PK, auto-incrémenté | Identifiant unique |
| `title` | `string` | NOT NULL | Titre de la leçon |

#### `words` — Mots / Signes

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | `integer` | PK, auto-incrémenté | Identifiant unique |
| `string` | `string` | NOT NULL | Texte du mot ou de l'expression |

#### `word_corespondance` — Correspondances modèle ↔ mots

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | `integer` | PK, auto-incrémenté | Identifiant unique |
| `label` | `string` | NOT NULL, UNIQUE, indexé | Label tel que reconnu par le modèle ONNX |
| `words` | `json` | NOT NULL, défaut `[]` | Liste des IDs de `words` associés |

### Tables d'association

| Table | Clés | Rôle |
|---|---|---|
| `lesson_words` | `lesson_id` → `lessons`, `word_id` → `words` | Mots inclus dans une leçon (many-to-many) |
| `user_lessons_done` | `user_id` → `users`, `lesson_id` → `lessons` | Leçons complétées par un utilisateur (many-to-many) |
| `word_corespondance_words` | `corespondance_id` → `word_corespondance`, `word_id` → `words` | Mots liés à une correspondance modèle (many-to-many) |

---

## Structure du projet

```
Signy-PIE/
├── frontend/
│   ├── src/
│   │   ├── api/              # Clients HTTP
│   │   ├── assets/           # Images, polices
│   │   ├── components/       # Composants Vue
│   │   ├── lib/              # MediaPipe, utilitaires
│   │   ├── router/           # Configuration des routes
│   │   ├── types/            # Types TypeScript partagés
│   │   ├── views/            # Pages (view-*.vue)
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   │   ├── icons/
│   │   └── mediapipe/        # Modèles WASM MediaPipe
│   ├── .env.example
│   ├── index.html
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/
│   ├── assets/
│   │   ├── modele_tcn.onnx   # Modèle TCN de reconnaissance
│   │   └── metadata.json     # Labels, normalisation, contrat d'entrée
│   ├── db/
│   │   ├── connection.py     # Session SQLAlchemy
│   │   ├── initialization.py # Création des tables au démarrage
│   │   ├── migrations.py     # Migrations légères
│   │   ├── models.py         # Modèles ORM (User, Lesson, Word…)
│   │   └── seed.py           # Données de démonstration
│   ├── routes/
│   │   ├── ai.py             # POST /ai/interrogate
│   │   ├── health.py         # GET /health
│   │   ├── lessons.py        # GET /lessons
│   │   ├── users.py          # GET /users
│   │   └── words.py          # GET /words
│   ├── schemas/
│   │   ├── ai.py             # AIPointsRequest, AIWordResponse
│   │   ├── catalog.py        # LessonListItem, LessonDetail, WordItem
│   │   └── users.py          # UserListItem, UserDetail
│   ├── services/
│   │   ├── interrogation.py  # Orchestration prédiction + validation
│   │   ├── prediction.py     # Chargement et inférence ONNX
│   │   └── preprocessing.py  # Normalisation des points MediaPipe
│   ├── utils/
│   │   ├── labels.py         # Résolution label ↔ index
│   │   └── serializers.py    # Helpers de sérialisation
│   ├── tests/
│   │   ├── test_ai_api.py
│   │   └── test_catalog_api.py
│   ├── .env.example
│   ├── config.py             # Chargement du .env
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── main.py               # Point d'entrée FastAPI
│   └── requirements.txt
│
├── package.json              # Workspace npm racine (lint, format)
├── AGENTS.md                 # Guide de travail pour les contributeurs/agents
└── README.md
```

---

## Commandes utiles

### Frontend (depuis la racine)

```sh
npm run dev --workspace frontend      # Serveur de développement
npm run build --workspace frontend    # Build de production
npm run type-check --workspace frontend # Vérification TypeScript
npm run lint                          # ESLint sur tout le projet
npm run format                        # Prettier sur tout le projet
```

### Backend (depuis `backend/`)

```sh
docker compose up --build           # Démarrer tous les services
docker compose down                 # Arrêter
docker compose logs -f              # Suivre les logs
docker compose exec backend python -m db.seed       # Seed de la base
docker compose exec backend python -m unittest discover -s tests -v  # Tests
```

---

## Vie privée et données

- **La vidéo reste dans le navigateur.** Elle n'est ni envoyée au serveur ni stockée.
- **Les points de squelette** (coordonnées MediaPipe) sont envoyés au serveur uniquement lors de la validation, puis immédiatement traités et **non persistés**.
- **Le modèle ne se réentraîne pas** à partir des exercices. Il utilise uniquement des données issues de l'entraînement initial, et sert uniquement à effectuer des prédictions.

---

## Contribuer

Nous manquons toujours de données pour améliorer la qualité de notre modèle.
Pour participer et nous aider voici le lien :
https://lsf-sign-yourself.vercel.app/
