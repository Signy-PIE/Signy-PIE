# Signy PIE

Signy PIE est une application pour découvrir et pratiquer la langue des signes française (LSF). Elle s’adresse notamment aux proches de personnes sourdes qui souhaitent apprendre des signes pour mieux communiquer au quotidien.

## Apprendre en pratiquant

L’application propose des leçons organisées autour de mots et d’expressions, ainsi qu’un lexique pour retrouver les mots du catalogue. Vous pouvez vous exercer devant votre caméra et obtenir un retour automatique sur le signe reconnu.

Pour réaliser un exercice :

1. Choisissez une leçon et découvrez le mot à travailler.
2. Autorisez l’accès à la caméra, puis déclenchez l’enregistrement de votre geste.
3. Regardez l’aperçu et recommencez si nécessaire.
4. Validez votre enregistrement pour lancer l’analyse.
5. Consultez le résultat et poursuivez l’exercice ou réessayez.

La reconnaissance compare le signe détecté au mot attendu. Elle porte sur les signes appris par le modèle et peut se tromper : le résultat ne constitue pas une évaluation complète de votre maîtrise de la LSF.

Le projet est en cours de développement. Le contenu pédagogique, les parcours et les fonctionnalités utilisateur continuent d’évoluer.

## Vos vidéos et vos données

La vidéo enregistrée reste dans votre navigateur pour vous permettre de revoir votre geste. **Elle n’est ni envoyée au serveur ni enregistrée dans la base de données.**

L’application calcule sur votre appareil des points décrivant la position des mains, du visage et du corps. Lorsque vous validez l’enregistrement, ces points sont envoyés au serveur avec les informations nécessaires à leur traitement et le mot attendu. Le serveur les utilise pour reconnaître le signe et vous répondre. Les points et les résultats de prédiction ne sont pas enregistrés dans la base de données.

**Les données de vos exercices — vidéos, points de mouvement et résultats — ne sont pas utilisées pour entraîner ou réentraîner le modèle d’IA.** L’application utilise un modèle déjà entraîné, uniquement pour effectuer des prédictions.

## Aperçu technique

Le traitement est réparti entre le navigateur et le serveur : le navigateur capture le geste et extrait les points de mouvement ; le serveur prépare ces points, exécute le modèle et renvoie le résultat.

| Partie | Rôle et technologies |
| --- | --- |
| Interface | Vue, TypeScript et Vite pour les leçons, le lexique et les exercices. |
| Analyse du mouvement | MediaPipe dans le navigateur pour extraire les points des mains, du visage et du corps. |
| Serveur | FastAPI et NumPy pour recevoir, vérifier et préparer les données. |
| Reconnaissance IA | Modèle ONNX exécuté avec ONNX Runtime pour identifier le signe. |
| Base de données | SQLAlchemy avec SQLite en local ou PostgreSQL selon la configuration, pour les mots, les leçons et les utilisateurs. |

Le code de l’interface se trouve dans [frontend/](frontend/) et celui du serveur dans [backend/](backend/). Les routes, le traitement IA et l’accès à la base sont séparés pour faciliter les évolutions du projet.

Les consignes de travail et les commandes de développement sont regroupées dans [AGENTS.md](AGENTS.md).
