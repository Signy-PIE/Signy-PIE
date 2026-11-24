from sqlalchemy.orm import Session

from db.connection import SessionLocal
from db.initialization import initialize_database
from db.models import Lesson, User, Word, WordCorespondance


# Remplit une base vide avec les données de démonstration sans modifier les données existantes.
def seed_database(db: Session) -> bool:
    if any(db.query(model).first() is not None for model in (Word, Lesson, User, WordCorespondance)):
        return False

    words = {i: Word(id=i, string=word) for i, word in enumerate(
        ("Âge", "Bonjour", "Coiffeur", "Habiter", "Non", "Prénom", "Merci"), start=1
    )}
    db.add_all(words.values())
    for i, (label, ids) in enumerate((
        ("age", [1]), ("bonjour-merci", [2, 7]), ("coiffeur", [3]),
        ("habiter", [4]), ("non", [5]), ("prenom", [6]),
    ), start=1):
        db.add(WordCorespondance(id=i, label=label, words=ids,
                                word_items=[words[word_id] for word_id in ids]))

    lessons = [
        Lesson(id=1, title="Les salutations", words=[words[2], words[7]]),
        Lesson(id=2, title="Les bases", words=[words[4], words[5]]),
        Lesson(id=3, title="Les expressions utiles", words=[words[1], words[6]]),
    ]
    db.add_all(lessons)
    db.add_all([
        User(id=1, nom="Dupont", prenom="Alice", email="alice@example.com",
             password="hashed_password_1", premium=True, lessons_done=[lessons[0]]),
        User(id=2, nom="Martin", prenom="Bob", email="bob@example.com",
             password="hashed_password_2", premium=False),
    ])
    db.commit()
    return True


# Crée les tables puis lance le seed à la demande avec python -m db.seed.
def main():
    initialize_database()
    with SessionLocal() as db:
        seed_database(db)


if __name__ == "__main__":
    main()
