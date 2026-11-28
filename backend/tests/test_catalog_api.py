from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.connection import get_db
from db.models import Lesson, User, Word, WordCorespondance
from main import app


class CatalogAPITests(unittest.TestCase):
    # Démarre l’API avec une base vide et isolée pour chaque test.
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        sessions = sessionmaker(bind=engine)
        self.sessions = sessions
        self.addCleanup(engine.dispose)

        # Fournit une session de la base en mémoire à la place de la base réelle.
        def test_db():
            with sessions() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.addCleanup(app.dependency_overrides.clear)
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch("db.initialization.engine", engine))
        self.client = stack.enter_context(TestClient(app))

    # Insère uniquement les données nécessaires aux tests du catalogue.
    def create_test_catalog(self):
        with self.sessions() as db:
            age = Word(id=1, string="Âge")
            bonjour = Word(id=2, string="Bonjour")
            merci = Word(id=7, string="Merci")
            lesson = Lesson(id=1, title="Salutations", words=[bonjour, merci])
            db.add_all([
                User(id=1, nom="Test", prenom="Utilisateur", email="test@example.com",
                     password="test", lessons_done=[lesson]),
                WordCorespondance(id=1, label="age", words=[1], word_items=[age]),
                WordCorespondance(id=2, label="bonjour-merci", words=[2, 7],
                                 word_items=[bonjour, merci]),
            ])
            db.commit()

    # Vérifie que le démarrage crée les tables sans ajouter de données.
    def test_startup_leaves_database_empty(self):
        self.assertEqual(self.client.get("/").json(),
                         {"message": "Signy PIE API is running"})
        for path in ("/users", "/lessons", "/words", "/word-corespondance",
                     "/word-correspondances"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), [])

    # Vérifie les listes, les détails et les champs publics des réponses imbriquées.
    def test_catalog_and_nested_responses(self):
        self.create_test_catalog()
        for path, count in (("/users", 1), ("/lessons", 1), ("/words", 3)):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(len(response.json()), count)
                item = response.json()[0]
                self.assertEqual(self.client.get(f"{path}/{item['id']}").json(), item)
        user = self.client.get("/users/1").json()
        self.assertEqual(set(user), {"id", "nom", "prenom", "email", "premium",
                                     "creation_date", "lessons_done"})
        self.assertEqual(user["lessons_done"][0]["words"],
                         [{"id": 2, "string": "Bonjour"}, {"id": 7, "string": "Merci"}])

    # Vérifie les deux URL de correspondances et la recherche par libellé ou mot.
    def test_correspondence_aliases_and_label_search(self):
        self.create_test_catalog()
        for prefix in ("/word-corespondance", "/word-correspondances"):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(len(response.json()), 2)
                item = self.client.get(f"{prefix}/2").json()
                self.assertEqual(item["words"], [2, 7])
                for label in ("bonjour-merci", "Bonjour", "Merci"):
                    self.assertEqual(self.client.get(f"{prefix}/by-label/{label}").json(), item)
                self.assertEqual(self.client.get(f"{prefix}/by-label/Âge").json()["id"], 1)

    # Vérifie qu’une ressource inconnue renvoie une erreur 404.
    def test_missing_resources_return_404(self):
        for path in ("/users/999", "/lessons/999", "/words/999",
                     "/word-corespondance/999", "/word-correspondances/999",
                     "/word-corespondance/by-label/inconnu",
                     "/word-correspondances/by-label/inconnu"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


if __name__ == "__main__":
    unittest.main()
