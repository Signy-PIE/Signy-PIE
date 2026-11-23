from sqlalchemy.orm import Session

from db.models import WordCorespondance
from schemas.catalog import WordCorespondanceDetail


# Prépare la réponse d’une correspondance avec les détails de ses mots associés.
def serialize_corespondance(item: WordCorespondance, db: Session) -> WordCorespondanceDetail:
    return WordCorespondanceDetail(
        id=item.id,
        label=item.label,
        words=item.words,
        matched_words=item.get_words(db),
    )
