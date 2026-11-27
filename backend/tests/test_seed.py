from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.connection import Base
from db.models import Lesson, User, Word, WordCorespondance
from db.seed import seed_database


class SeedTests(unittest.TestCase):
    # Prépare une base SQLite en mémoire pour chaque test du seed.
    def setUp(self):
        self.engine = create_engine("sqlite://")
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)

    # Vérifie les données et associations créées, puis l’absence de doublons au second appel.
    def test_seed_creates_demo_catalog_once(self):
        with Session(self.engine) as db:
            self.assertTrue(seed_database(db))
            self.assertFalse(seed_database(db))
            for model, count in ((Word, 7), (Lesson, 3), (User, 2), (WordCorespondance, 6)):
                self.assertEqual(db.query(model).count(), count)
            self.assertEqual([word.id for word in db.get(Lesson, 1).words], [2, 7])
            self.assertEqual([lesson.id for lesson in db.get(User, 1).lessons_done], [1])
            self.assertEqual([word.id for word in db.get(WordCorespondance, 2).get_words(db)],
                             [2, 7])

    # Vérifie qu’une base contenant déjà des données reste inchangée.
    def test_seed_preserves_existing_database(self):
        with Session(self.engine) as db:
            db.add(Word(id=42, string="Existant"))
            db.commit()
            self.assertFalse(seed_database(db))
            self.assertEqual([(word.id, word.string) for word in db.query(Word)],
                             [(42, "Existant")])
            for model in (Lesson, User, WordCorespondance):
                self.assertEqual(db.query(model).count(), 0)


if __name__ == "__main__":
    unittest.main()
