# Signy PIE

Signy PIE est une application pour apprendre la **langue des signes française (LSF)**
et pratiquer des signes devant sa caméra, avec un retour automatique grâce à l’intelligence artificielle.

Elle s’adresse notamment aux proches de personnes sourdes ou malentendantes qui souhaitent
mieux communiquer au quotidien.

## Fonctionnalités

- **Leçons guidées** : pratiquer les mots d’une leçon, un signe à la fois.
- **Exercices avec la caméra** : enregistrer son geste, le revoir et recommencer si nécessaire.
- **Reconnaissance des signes** : obtenir le signe reconnu et savoir s’il correspond au mot demandé.
- **Lexique** : retrouver les mots du catalogue grâce à une recherche et un classement alphabétique.
- **Installation sur mobile** : ajouter l’application à son écran d’accueil.

## Comment se déroule un exercice ?

1. Choisir une leçon et découvrir le mot à signer.
2. Activer la caméra et enregistrer son geste.
3. Revoir l’enregistrement, puis choisir « Utiliser cette vidéo » ou recommencer.
4. Recevoir le résultat de l’analyse et passer au mot suivant lorsque le signe est validé.

## Vie privée

La vidéo reste temporairement dans le navigateur pour permettre sa relecture ; elle n’est pas
transmise au serveur. Après validation par l’utilisateur, seules les coordonnées des mouvements
sont envoyées pour l’analyse. Ces coordonnées et les résultats ne sont pas enregistrés en base.
Les exercices ne servent pas à entraîner ou réentraîner le modèle.

## État du projet

L’application est en cours de développement. Les leçons, les exercices et le lexique constituent
le parcours actuel. La gestion des comptes et la sauvegarde de la progression restent à finaliser.

## Contribuer

Pour contribuer à la collecte de vidéos destinée à améliorer le modèle, un parcours distinct
est proposé sur [Sign Yourself](https://lsf-sign-yourself.vercel.app/).

## Documentation technique

- [Frontend : interface et capture vidéo](docs/README-frontend.md)
- [Backend : installation, API et base de données](docs/README-backend.md)
- [Modèle IA : reconnaissance et prétraitement](docs/README-modele.md)
