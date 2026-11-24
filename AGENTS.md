# Guide de travail — Signy PIE

## Objectif du projet

Signy PIE est une application pour apprendre la langue des signes française, avec des leçons et une reconnaissance de signes par IA.

- Public visé : Proches de personnes sourdes ou muettes
- Fonctionnalités prioritaires : Reconnaissance des gestes grace à un modele de reconnaissance video
- Travail en cours : Création de l'application d'apprentissage, des lecons, parcours et fonctions utilisateur

## Architecture

- `frontend/` : Vue, TypeScript, Vite et extraction des points MediaPipe.
- `backend/main.py` : initialisation FastAPI et enregistrement des routes.
- `backend/config.py` : chargement de `backend/.env`.
- `backend/routes/` : endpoints HTTP et gestion des erreurs.
- `backend/services/` : prétraitement des points et prédiction ONNX.
- `backend/db/` : connexion, modèles SQLAlchemy, migration et seed local.
- `backend/schemas/` : validation des requêtes et réponses avec Pydantic.
- `backend/utils/` : fonctions utilitaires communes.
- `backend/assets/` : modèle ONNX et métadonnées associées.
- `backend/tests/` : tests du backend.

Le `README.md` décrit l’installation et l’utilisation du projet.

## Parcours des données

1. L’utilisateur déclenche la capture vidéo dans le navigateur.
2. Le frontend extrait les coordonnées MediaPipe : mains, pose et visage.
3. L’utilisateur revoit puis valide sa vidéo.
4. Le frontend envoie automatiquement les points, leurs masques de présence, la cadence et le mot attendu à `POST /ai/interrogate`.
5. Le backend prétraite les points, exécute le modèle ONNX et renvoie la prédiction et la validation.

Le backend reçoit des points, pas la vidéo complète. Il n’y a plus de vidéos de référence dans le parcours.

Contrat actuel : 96 points par image, entrée ONNX `float32 (1, 90, 350)`. Le modèle et `metadata.json` doivent rester cohérents avec le prétraitement.

## Conventions de travail

- Garder un code simple, concis et lisible.
- Faire des changements ciblés et respecter les modifications déjà présentes.
- Garder la logique métier dans les services et les routes courtes.
- Conserver les noms de vues frontend sous la forme `view-*.vue`.
- Ne pas versionner de secrets : utiliser `backend/.env` et maintenir un `.env.example` sans identifiants réels.
- Le seed sert de test, la DB finale sera configurée prochainement

## Commandes utiles

Frontend, depuis la racine :

```sh
npm install
npm run dev --workspace frontend
```

Backend, depuis `backend/`, avec le venv activé :

```sh
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Seed local facultatif, depuis `backend/` :

```sh
python -m db.seed
```

Cette commande utilise `DATABASE_URL` si elle est définie, sinon la base SQLite locale `backend/signy.db`.

Docker, depuis la racine :

```sh
docker compose --env-file backend/.env up --build
```

## Vérifications

Adapter les vérifications aux fichiers modifiés et signaler celles qui n’ont pas pu être exécutées.

Backend, depuis `backend/` :

```sh
python -m unittest discover -s tests -v
```

Frontend, depuis la racine :

```sh
npm run lint
npm run type-check --workspace frontend
npm run build --workspace frontend
```

## Points à préciser

- Critères de validation d’une fonctionnalité : Accessible, fonctionnelle, gestion des erreurs, sécurisée
- Contraintes de déploiement et environnements utilisés : travail à plusieurs donc respect des nomenclatures, changement petit à petit
