# Frontend — Signy PIE

[Présentation du projet](../README.md) · [Backend](README-backend.md) · [Modèle IA](README-modele.md)

Le frontend affiche les leçons et le lexique, gère les exercices avec la caméra et extrait
les points du mouvement avant leur envoi à l’API.

## Technologies

Vue 3, TypeScript, Vite et Vue Router. MediaPipe Tasks Vision détecte les mains, la pose et
le visage dans le navigateur. Le plugin Vite PWA permet l’installation de l’application.

## Installation et démarrage

Prérequis : Node.js conforme à `^22.18.0 || >=24.11.0` et npm.
Depuis la racine du dépôt :

```sh
npm install
npm run dev --workspace frontend
```

L’interface est accessible sur <http://localhost:5173>. Démarrer aussi le
[backend](README-backend.md) pour charger le catalogue et analyser les gestes.

## Configuration de l’API

Sans configuration, le frontend appelle `http://localhost:8000`.
Pour changer cette adresse, copier `frontend/.env.example` vers `frontend/.env.local`
et définir :

```dotenv
VITE_API_URL=http://localhost:8000
```

Pour passer par le proxy Vite, notamment lors d’un test sur téléphone avec un tunnel HTTPS :

```dotenv
VITE_API_URL=/api
```

Le proxy redirige `/api` vers `http://localhost:8000` et retire le préfixe.
Redémarrer Vite après modification. La caméra nécessite une autorisation du navigateur
et un accès en HTTPS ou sur `localhost`.

## Organisation

| Chemin dans `frontend/` | Rôle |
| --- | --- |
| `src/views/view-*.vue` | Accueil, leçon, lexique et profil |
| `src/components/` | Composants partagés et interface de capture |
| `src/api/api.ts` | Appels HTTP vers le backend |
| `src/lib/landmarkExtractor.ts` | Extraction des 96 points MediaPipe par image |
| `src/types/` | Types des leçons, mots et captures |
| `src/router/index.ts` | Routes de l’application |
| `public/mediapipe/` | Détecteurs et fichiers WASM servis localement |
| `vite.config.ts` | Configuration Vite, proxy et PWA |

Les routes principales sont `/home`, `/lesson/:lessonId`, `/lexique` et `/profile`.
Le formulaire de profil est une démonstration locale : il ne crée pas de compte sur le serveur.

## Capture et analyse

1. `videoCard.vue` active la caméra et prépare les détecteurs MediaPipe.
2. Pendant l’enregistrement, il collecte les points et produit une vidéo temporaire pour la relecture.
3. Après « Utiliser cette vidéo », `videoBlock.vue` demande l’analyse via `src/api/api.ts`.
4. Le client envoie `points`, `valid`, `fps` et `expected_word` à `POST /ai/interrogate`.
5. L’interface affiche la validation du mot ou un message permettant de réessayer.

La vidéo n’est pas envoyée. Les erreurs de caméra, de capture et d’analyse sont affichées
à l’utilisateur ; la requête d’analyse est interrompue au bout de 30 secondes.
Le format des points est détaillé dans le [README du modèle](README-modele.md).

## Vérifications et build

Depuis la racine :

```sh
npm run lint
npm run type-check --workspace frontend
npm run build --workspace frontend
```

Le build produit `frontend/dist/`. Pour le prévisualiser :

```sh
npm run preview --workspace frontend
```

Le formatage est partagé à la racine avec ESLint et Prettier. Conserver les noms de vues `view-*.vue`.
