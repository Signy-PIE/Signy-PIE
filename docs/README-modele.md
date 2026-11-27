# Modèle IA — Signy PIE

[Présentation du projet](../README.md) · [Frontend](README-frontend.md) · [Backend](README-backend.md)

L’application utilise un modèle TCN (*Temporal Convolutional Network*) déjà entraîné,
exporté au format ONNX. Il reconnaît un signe à partir d’une séquence de mouvements.
Ce dépôt contient l’inférence et le prétraitement, pas la chaîne d’entraînement du modèle.

## Fichiers utilisés

| Fichier | Rôle |
| --- | --- |
| `backend/assets/modele_tcn.onnx` | Modèle exécuté sur CPU avec ONNX Runtime |
| `backend/assets/metadata.json` | Classes, dimensions d’entrée et statistiques de standardisation |
| `frontend/src/lib/landmarkExtractor.ts` | Extraction des points MediaPipe dans le navigateur |
| `backend/services/preprocessing.py` | Transformation des points en entrée ONNX |
| `backend/services/prediction.py` | Chargement du modèle et calcul de la prédiction |
| `backend/services/interrogation.py` | Comparaison du signe prédit au mot attendu |

## Contrat actuel

| Paramètre | Valeur |
| --- | --- |
| Points par image | 96 points de 3 coordonnées `(x, y, z)` |
| Séquence reçue par l’API | `points (T, 96, 3)`, `valid (T, 96)` et `fps > 0` |
| Longueur acceptée par l’API | 5 à 1 800 images |
| Identifiant de prétraitement | `mediapipe96-geometrie175-v1` |
| Entrée ONNX | `float32 (1, 90, 350)` |
| Caractéristiques par image | 175 valeurs géométriques, puis 175 masques d’observation |
| Sortie ONNX | Logits de forme `(1, 78)` |
| Classes | 78, dans l’ordre de `metadata.json` |

### Ordre des points

Les indices sont comptés à partir de zéro :

| Indices | Groupe |
| --- | --- |
| `0–20` | 21 points de la main gauche |
| `21–41` | 21 points de la main droite |
| `42–74` | 33 points de pose |
| `75–95` | 21 points du visage sélectionnés |

Indices MediaPipe du visage, dans cet ordre :

```text
61, 291, 13, 14, 78, 308, 70, 105, 300, 334, 33, 133, 362, 263, 1, 4, 5, 10, 152, 234, 454
```

Chaque point absent vaut `[0, 0, 0]` et son masque `valid` vaut `false`.
Le frontend transmet les coordonnées des détecteurs ; la normalisation géométrique est faite côté backend.

## Prétraitement et prédiction

1. Vérifier les dimensions, les masques, les coordonnées et la cadence.
2. Garder la période où les mains sont détectées, avec une marge avant et après le geste.
3. Centrer et mettre à l’échelle les coordonnées XY à partir des épaules.
4. Rééchantillonner la séquence sur 90 images.
5. Calculer les 175 caractéristiques : positions locales des mains, angles, distances, vitesses et relations.
6. Standardiser avec les vecteurs `mean` et `std` de 175 valeurs, limiter les valeurs à `[-6, 6]`,
   puis ajouter les 175 masques d’observation.
7. Exécuter le modèle sur le tenseur `(1, 90, 350)` et appliquer un softmax aux logits.
8. Choisir la classe au score le plus élevé et la comparer au mot attendu.

La comparaison ignore la casse, les accents et les espaces en début et fin de mot.
Le mot attendu doit lui-même correspondre à une classe connue du modèle après cette normalisation.
`is_valid` dépend de cette comparaison ; aucun seuil de confiance n’est appliqué.
Le champ `confidence` est le score softmax de la classe choisie, pas une mesure d’exactitude du modèle.

## Prétraiter une capture hors de l’API

Avec les dépendances backend installées, depuis `backend/` :

```sh
python -m services.preprocessing capture.json --sortie entree.npy
```

Le fichier JSON doit contenir `points`, `valid` et `fps` au format décrit ci-dessus.
La commande produit le tenseur NumPy d’entrée ; elle n’exécute pas la reconnaissance.
Elle permet aussi de préciser les métadonnées avec `--metadata chemin/metadata.json`.

## Remplacer le modèle

Remplacer ensemble le fichier ONNX et ses métadonnées. Les chemins peuvent être configurés
avec `AI_MODEL_PATH` et `AI_METADATA_PATH`, puis nécessitent un redémarrage du backend.

Le chargeur vérifie l’identifiant de prétraitement, les statistiques, le type et la forme d’entrée,
les libellés et la dimension de sortie. Un modèle utilisant d’autres points ou caractéristiques
nécessite également d’adapter l’extraction et le prétraitement.

`GET /health` déclenche le chargement et indique le fichier utilisé et son nombre de classes.
Un modèle indisponible ou incompatible renvoie `503`. Une capture inexploitable ou un mot
non pris en charge renvoie `422` lors de l’analyse.

Les exercices ne modifient pas le modèle. Aucune métrique d’évaluation n’est fournie dans
les métadonnées livrées ; les performances doivent être mesurées sur un jeu de test distinct.
