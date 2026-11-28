from pathlib import Path
import sys
import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.connection import Base
from db.migrations import remove_reference_videos
from db.models import Lesson, User, Word


class ReferenceVideoRemovalTests(unittest.TestCase):
    # Vérifie que la migration conserve les mots, les leçons et la progression existante.
    def test_existing_words_and_relationships_are_preserved(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        with engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            for sql in (
                "CREATE TABLE videos (id INTEGER PRIMARY KEY, url VARCHAR NOT NULL)",
                "CREATE TABLE words (id INTEGER PRIMARY KEY, string VARCHAR NOT NULL, "
                "video_id INTEGER NOT NULL, FOREIGN KEY(video_id) REFERENCES videos(id))",
                "CREATE INDEX ix_words_id ON words(id)",
                "CREATE TABLE lessons (id INTEGER PRIMARY KEY, title VARCHAR NOT NULL)",
                "CREATE TABLE lesson_words (lesson_id INTEGER REFERENCES lessons(id), "
                "word_id INTEGER REFERENCES words(id), PRIMARY KEY(lesson_id, word_id))",
                "INSERT INTO videos VALUES (1, 'ancienne-reference')",
                "INSERT INTO words VALUES (12, 'Bonjour', 1), (27, 'Merci', 1)",
                "INSERT INTO lessons VALUES (3, 'Salutations')",
                "INSERT INTO lesson_words VALUES (3, 12), (3, 27)",
            ):
                connection.exec_driver_sql(sql)

        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(User(id=8, nom="Test", prenom="Utilisateur", email="test@example.com",
                        password="test", lessons_done=[db.get(Lesson, 3)]))
            db.commit()

        remove_reference_videos(engine)
        remove_reference_videos(engine)

        Base.metadata.create_all(engine)
        self.assertFalse(inspect(engine).has_table("videos"))
        self.assertEqual({c["name"] for c in inspect(engine).get_columns("words")}, {"id", "string"})
        with Session(engine) as db:
            self.assertEqual([(w.id, w.string) for w in db.query(Word).order_by(Word.id)],
                             [(12, "Bonjour"), (27, "Merci")])
            self.assertEqual(db.execute(text("SELECT * FROM lesson_words ORDER BY word_id")).all(),
                             [(3, 12), (3, 27)])
            self.assertEqual(db.execute(text("SELECT title FROM lessons WHERE id=3")).scalar(),
                             "Salutations")
            self.assertEqual([lesson.id for lesson in db.get(User, 8).lessons_done], [3])
            self.assertEqual(db.execute(text("PRAGMA foreign_keys")).scalar(), 1)
            self.assertEqual(db.execute(text("PRAGMA foreign_key_check")).all(), [])
            db.add(Word(id=40, string="Âge"))
            db.commit()
        engine.dispose()

    # Vérifie qu’une base neuve reste vide et ne contient aucune référence vidéo.
    def test_fresh_database_has_no_reference_videos(self):
        engine = create_engine("sqlite://")
        remove_reference_videos(engine)
        Base.metadata.create_all(engine)
        remove_reference_videos(engine)
        self.assertFalse(inspect(engine).has_table("videos"))
        self.assertNotIn("video_id", {c["name"] for c in inspect(engine).get_columns("words")})
        with Session(engine) as db:
            self.assertEqual(db.query(Word).count(), 0)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
