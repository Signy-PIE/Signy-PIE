# Backend — Signy PIE

[Présentation du projet](../README.md) · [Frontend](README-frontend.md) · [Modèle IA](README-modele.md)

Le backend expose le catalogue, les leçons et les utilisateurs. Il reçoit les points MediaPipe,
les prétraite et exécute le modèle ONNX pour vérifier le signe attendu.

## Technologies et organisation

FastAPI et Uvicorn pour l’API, Pydantic pour la validation, SQLAlchemy pour la base de données,
NumPy pour le prétraitement et ONNX Runtime pour la prédiction sur CPU.

| Chemin dans `backend/` | Rôle |
| --- | --- |
| `main.py` | Initialisation de FastAPI et enregistrement des routes |
| `config.py` | Chargement de `backend/.env` |
| `routes/` | Endpoints HTTP et traduction des erreurs |
| `services/` | Logique métier, prétraitement et prédiction |
| `schemas/` | Validation des requêtes et réponses |
| `db/` | Connexion, modèles, migration et seed |
| `utils/` | Normalisation des libellés et sérialisation |
| `assets/` | Modèle ONNX et métadonnées |
| `tests/` | Tests du backend |

## Démarrage local

Utiliser Python 3.12 pour suivre la version du Dockerfile. Depuis la racine :

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Sans `DATABASE_URL`, la base locale est `backend/signy.db` (SQLite).
Les tables sont créées au démarrage ; le seed n’est pas exécuté automatiquement.

- API : <http://localhost:8000>
- Documentation interactive : <http://localhost:8000/docs>

Dans un autre terminal, depuis `backend/` avec le même environnement activé :

```sh
python -m db.seed
```

Le seed ajoute des données de démonstration uniquement si les tables métier sont vides.
Il ne modifie pas une base déjà remplie. Il sert aux tests et au développement ;
la base définitive reste à configurer.

## Démarrage avec Docker

Prérequis : Docker et Docker Compose. Depuis la racine :

```sh
cd backend
cp .env.example .env
```

Renseigner les valeurs PostgreSQL et pgAdmin dans `.env`, puis lancer depuis `backend/` :

```sh
docker compose up --build
```

Compose démarre PostgreSQL 16, le backend Python 3.12 et pgAdmin.
Le frontend se lance séparément selon son [README](README-frontend.md).

| Service | Adresse locale |
| --- | --- |
| API et documentation | <http://localhost:8000/docs> |
| PostgreSQL | `localhost:5432` |
| pgAdmin | <http://localhost:5050> |

Commandes depuis `backend/` :

```sh
docker compose exec backend python -m db.seed
docker compose exec backend python -m unittest discover -s tests -v
docker compose logs -f
docker compose down
```

Les données PostgreSQL et pgAdmin sont conservées dans des volumes Docker.

### Consulter les tables avec pgAdmin

Se connecter à <http://localhost:5050> avec `PGADMIN_DEFAULT_EMAIL` et `PGADMIN_DEFAULT_PASSWORD`.
Ajouter un serveur et renseigner sa connexion :

| Champ | Valeur |
| --- | --- |
| Host name/address | `db` |
| Port | `5432` |
| Maintenance database | Valeur de `POSTGRES_DB` |
| Username | Valeur de `POSTGRES_USER` |
| Password | Valeur de `POSTGRES_PASSWORD` |

L’hôte est `db`, car pgAdmin et PostgreSQL sont dans le même réseau Compose.
Les tables sont accessibles sous `Databases → <base> → Schemas → public → Tables`.
Un clic droit puis **View/Edit Data → All Rows** permet de consulter leur contenu.

## Variables d’environnement

`config.py` charge `backend/.env`. Les variables déjà définies dans l’environnement ont priorité.
Ne pas versionner ce fichier ; conserver les exemples sans identifiants réels dans `.env.example`.

| Variable | Utilisation / valeur par défaut |
| --- | --- |
| `DATABASE_URL` | Connexion SQLAlchemy ; SQLite local si absente |
| `POSTGRES_DB` | Nom de la base, requis par Compose |
| `POSTGRES_USER` | Utilisateur PostgreSQL, requis par Compose |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL, requis par Compose |
| `PGADMIN_DEFAULT_EMAIL` | Identifiant pgAdmin, requis par Compose |
| `PGADMIN_DEFAULT_PASSWORD` | Mot de passe pgAdmin, requis par Compose |
| `AI_MODEL_PATH` | Facultatif ; `backend/assets/modele_tcn.onnx` |
| `AI_METADATA_PATH` | Facultatif ; `metadata.json` à côté du modèle |

Compose définit lui-même `DATABASE_URL` avec l’hôte `db` et les chemins du modèle dans `/app/assets/`.
Pour joindre PostgreSQL depuis un backend lancé hors Docker, utiliser une URL de cette forme :

```dotenv
DATABASE_URL=postgresql+psycopg2://utilisateur:mot_de_passe@localhost:5432/signy
```

## API

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/` | Confirmer que l’API répond |
| `GET` | `/health` | Vérifier le chargement du modèle et renvoyer son nombre de classes |
| `GET` | `/lessons` et `/lessons/{lesson_id}` | Consulter les leçons et leurs mots |
| `GET` | `/words` et `/words/{word_id}` | Consulter le catalogue |
| `GET` | `/users` et `/users/{user_id}` | Consulter les utilisateurs et leurs leçons terminées |
| `GET` | `/word-correspondances` | Lister les correspondances entre libellés et mots |
| `GET` | `/word-correspondances/{corespondance_id}` | Consulter une correspondance |
| `GET` | `/word-correspondances/by-label/{label}` | Rechercher une correspondance par libellé ou alias |
| `POST` | `/ai/interrogate` | Reconnaître le signe et le comparer au mot attendu |

Les routes de correspondance existent aussi sous l’ancien préfixe `/word-corespondance`.
La gestion des comptes n’est pas encore implémentée : les routes utilisateurs sont en lecture seule.

### Requête d’analyse

Le corps JSON contient les champs suivants :

| Champ | Format |
| --- | --- |
| `points` | Tableau `(T, 96, 3)` de coordonnées numériques finies |
| `valid` | Tableau `(T, 96)` de booléens indiquant les points détectés |
| `fps` | Cadence de capture, strictement positive |
| `expected_word` | Mot attendu, de 1 à 100 caractères |

L’API accepte de 5 à 1 800 images. Le [README du modèle](README-modele.md) précise
l’ordre des points et le prétraitement.

La réponse contient `word`, `label`, `true_label`, `confidence`, `matched_word_ids`,
`matched_words`, `is_valid`, `tested_word` et `message`. `is_valid` indique si le signe reconnu
correspond au mot demandé ; une non-correspondance reste une réponse HTTP `200`.

| Code | Signification |
| --- | --- |
| `404` | Ressource du catalogue introuvable |
| `422` | Requête invalide, capture inexploitable ou mot absent des classes du modèle |
| `503` | Modèle indisponible ou échec de l’inférence |

## Base de données

Les modèles se trouvent dans `db/models.py`.

| Table | Données principales |
| --- | --- |
| `users` | `id`, `nom`, `prenom`, `email` unique, `password`, `premium`, `creation_date` |
| `lessons` | `id`, `title` |
| `words` | `id`, `string` |
| `word_corespondance` | `id`, `label` unique, `words` (liste JSON d’identifiants) |
| `lesson_words` | Association entre leçons et mots |
| `user_lessons_done` | Association entre utilisateurs et leçons terminées |
| `word_corespondance_words` | Association entre correspondances et mots |

```mermaid
erDiagram
    users ||--o{ user_lessons_done : termine
    lessons ||--o{ user_lessons_done : concerne
    lessons ||--o{ lesson_words : contient
    words ||--o{ lesson_words : appartient
    word_corespondance ||--o{ word_corespondance_words : regroupe
    words ||--o{ word_corespondance_words : reference
```

Au démarrage, `db/initialization.py` applique la migration supprimant les anciennes références
vidéo (`words.video_id` et table `videos`), puis crée les tables manquantes.
L’analyse IA ne sauvegarde ni vidéo, ni points, ni résultat en base et ne réentraîne pas le modèle.

## Tests locaux

Depuis `backend/`, avec le venv activé :

```sh
python -m unittest discover -s tests -v
```
