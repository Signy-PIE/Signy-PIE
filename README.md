# Signy PIE

Signy PIE est une application pédagogique pour apprendre la langue des signes française (LSF). Le projet est découpé en deux parties principales : un frontend Vue 3 / Vite pour l'interface utilisateur, et un backend FastAPI pour l'API, les données et la prédiction IA sur vidéo.

## Vue d'ensemble

L'application propose :

- des leçons interactives pour progresser étape par étape,
- un enregistrement vidéo in-app pour s'exercer,
- une route IA qui analyse les keypoints MediaPipe et renvoie une prédiction,
- une validation automatique avec feedback (Bravo / Réessayez).

## Architecture

- **Frontend** : [frontend/](frontend) — Vue 3 + Vite + TypeScript.
- **Backend** : [backend/](backend) — FastAPI, SQLAlchemy, modèle ONNX.
- **Base de données** : SQLite en local si `DATABASE_URL` absent, PostgreSQL via Docker Compose.
- **pgAdmin** : interface graphique PostgreSQL accessible sur `http://localhost:5050`.

Le frontend appelle le backend sur `http://localhost:8000`.

## Prérequis

- Node.js 22.18+ (branche 22) ou 24.11+ et npm. Node.js 24 LTS à jour est recommandé.
- Python 3.12+.
- Docker et Docker Compose (recommandé).

---

## Lancer le projet avec Docker (recommandé)

```sh
docker compose up --build
```

Services exposés :

| Service | URL |
|---------|-----|
| Backend FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| pgAdmin | http://localhost:5050 |

### Connexion pgAdmin

Ouvre http://localhost:5050 puis connecte-toi avec :

- **Email** : `admin@signy.com`
- **Password** : `admin`

Enregistre le serveur PostgreSQL (**Register → Server**) avec :

| Champ | Valeur |
|-------|--------|
| Host | `db` *(nom du service Docker, pas `localhost`)* |
| Port | `5432` |
| Database | `signy` |
| Username | `signy` |
| Password | `signy` |

---

## Lancer le backend en local (sans Docker)

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Sans `DATABASE_URL`, le backend utilise SQLite (`backend/signy.db`). Les tables sont créées automatiquement au démarrage, sans ajout de données.

## Lancer le frontend en local

```sh
npm install
npm run dev --workspace frontend
# Disponible sur http://localhost:5173
```

L'installation se fait à la racine. ESLint et Prettier y sont centralisés, avec un seul `package-lock.json`.

Les outils JavaScript disposent de dépendances natives pour Linux, Windows et macOS. Le fichier `.npmrc` active leur installation et le verrouillage inclut leurs variantes par plateforme. Chaque machine doit installer ses propres dépendances ; ne partage pas le dossier `node_modules` entre systèmes ou avec WSL.

Si Rolldown signale un binaire manquant sous Windows, récupère le `package-lock.json` à jour, puis lance ces commandes dans PowerShell, depuis la racine :

```powershell
Remove-Item -Recurse -Force node_modules, frontend/node_modules -ErrorAction SilentlyContinue
npm ci --include=optional
npm run dev --workspace frontend
```

Conserve le fichier `package-lock.json` réparé.

---

## Commandes utiles

```bash
# Qualité du code (depuis la racine)
npm run lint
npm run lint:fix
npm run format
npm run format:check

# Frontend
cd frontend
npm run dev       # Dev avec hot-reload
npm run build     # Build de production (dist/)
npm run lint      # ESLint
npm run format    # Prettier

# Backend (dans le venv)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker compose up --build   # Démarrer tous les services
docker compose down         # Arrêter
docker compose logs -f      # Logs en temps réel

# Inspecter PostgreSQL directement
docker compose exec db psql -U signy -d signy
```

---

## API backend

Base URL : `http://localhost:8000`

### Endpoints disponibles

#### Health

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Vérification que l'API tourne |

#### Users

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/users` | Liste tous les utilisateurs |
| `GET` | `/users/{user_id}` | Détail d'un utilisateur (avec `lessons_done`) |

#### Lessons

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/lessons` | Liste toutes les leçons |
| `GET` | `/lessons/{lesson_id}` | Détail d'une leçon avec ses mots |

#### Words

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/words` | Liste tous les mots |
| `GET` | `/words/{word_id}` | Détail d'un mot |

#### Word Correspondance

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/word-corespondance` | Liste toutes les correspondances signe → mots |
| `GET` | `/word-corespondance/{id}` | Détail d'une correspondance |
| `GET` | `/word-corespondance/by-label/{label}` | Recherche par label du modèle |

#### IA

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/health` | Vérifie le chargement du modèle et de ses métadonnées |
| `POST` | `/ai/interrogate` | Prétraite les points MediaPipe, prédit le signe et compare au mot attendu |

Le front envoie le JSON suivant uniquement après validation de la vidéo :

| Champ | Type | Description |
|-------|------|-------------|
| `points` | `number[T][96][3]` | Coordonnées brutes `x, y, z` des mains, de la pose et du visage |
| `valid` | `boolean[T][96]` | Présence de chaque point |
| `fps` | `number` | Cadence réelle de capture, positive et finie |
| `expected_word` | `string` | Mot attendu, par exemple `Bonjour` |

La capture contient entre 5 et 1800 images. Aucune vidéo n'est envoyée au serveur.
Le backend applique le prétraitement NumPy, exécute ONNX puis renvoie la réponse ci-dessous.
Les accents et la casse sont ignorés pour comparer les labels ; Bonjour et Merci restent
**deux classes distinctes**, indépendamment des anciennes correspondances en base.

- `422` : données invalides, mains absentes, épaules inutilisables ou mot non appris.
- `503` : modèle indisponible ou échec de l'inférence.

Les erreurs métier sont renvoyées sous la forme `{"detail": "message"}`.
Le front abandonne l'attente après 30 secondes ; cela n'interrompt pas un calcul déjà démarré sur le serveur.

**Réponse 200 :**
```json
{
  "word": "age",
  "confidence": 0.97,
  "label": "age",
  "matched_word_ids": [1],
  "matched_words": ["Âge"],
  "is_valid": true,
  "tested_word": "Âge",
  "message": "Le signe reconnu correspond à 'Âge'."
}
```

---

## Modèle IA

- **Modèle** : `backend/assets/modele_tcn.onnx`
- **Métadonnées** : `backend/assets/metadata.json` : ordre des 78 classes, statistiques et version du prétraitement
- **Prétraitement** : `backend/services/preprocessing.py`, avec NumPy uniquement
- **Entrée ONNX** : `float32 (1, 90, 350)` : 175 caractéristiques géométriques et 175 masques d'observation
- **Sortie** : 78 logits, transformés en scores par softmax

Le modèle et les métadonnées sont chargés au premier appel puis conservés en mémoire.
`AI_MODEL_PATH` et `AI_METADATA_PATH` permettent de préciser leurs chemins.
Un chargement impossible renvoie une erreur ; aucune prédiction factice n'est produite.

La table historique `word_corespondance` reste consultable,
mais elle n'intervient plus dans la validation IA.
Le modèle choisit parmi les signes appris ; son score ne mesure pas la qualité du geste.

Pour tester les routes avec une base en mémoire et le vrai modèle, depuis `backend/` :

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

La page locale `/test-capture/`, ignorée par Git, permet également de saisir un mot,
enregistrer une vidéo, revoir l'aperçu puis envoyer les points avec « Utiliser cette vidéo ».

---

## Base de données

Le démarrage crée les tables sans insérer de données. Les données existantes sont conservées.
La migration retire l’ancienne colonne `words.video_id` et la table `videos`, en conservant
les mots et leurs associations aux leçons.

Les mots renvoyés par l’API contiennent uniquement `id` et `string`.

---

## Structure du projet

```text
Signy-PIE/
├── docker-compose.yml          # PostgreSQL + Backend + pgAdmin
├── package.json                # Monorepo root
├── backend/
│   ├── main.py                 # Application FastAPI et branchement des routes
│   ├── routes/                 # Santé, utilisateurs, leçons, mots, correspondances, IA
│   ├── services/               # Prétraitement, prédiction ONNX, recherche de correspondances
│   ├── db/                     # Connexion, modèles SQLAlchemy et migration
│   ├── schemas/                # Schémas Pydantic des requêtes et réponses
│   ├── utils/                  # Normalisation des libellés et sérialisation
│   ├── assets/                 # modele_tcn.onnx et metadata.json
│   ├── tests/                  # Tests API, modèle et migration
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── views/              # Pages : home, lexique, profile
    │   ├── components/         # Composants réutilisables
    │   ├── api/api.ts          # Client HTTP vers le backend
    │   ├── types/              # Types TypeScript
    │   └── router/             # Vue Router
    ├── vite.config.ts
    └── package.json
```

---

## Stack technique

| Couche | Technologie |
|--------|------------|
| Frontend | Vue 3, Vite, TypeScript |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| IA | ONNX Runtime (backend), MediaPipe pose/mains/visage (frontend) |
| Base de données | PostgreSQL (prod) / SQLite (dev) |
| DevOps | Docker, Docker Compose |
| Admin DB | pgAdmin 4 |

---

## Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Vue 3 Guide** : https://vuejs.org
- **Vite** : https://vitejs.dev
