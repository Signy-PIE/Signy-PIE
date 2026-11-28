from typing import Optional

from sqlalchemy.orm import Session

from db.models import WordCorespondance
from utils.labels import normalize_label


# Recherche une correspondance par libellé, sous-libellé ou mot associé.
def find_corespondance_by_label(db: Session, label: str) -> Optional[WordCorespondance]:
    if not label:
        return None
    norm = normalize_label(label)

    all_items = db.query(WordCorespondance).all()

    # 1. Exact match on label
    for item in all_items:
        if normalize_label(item.label) == norm:
            return item

    # 2. Check if normalized label matches any sub-label separated by '/' or '_'
    for item in all_items:
        parts = [normalize_label(p) for p in item.label.replace("_", "/").split("/")]
        if norm in parts:
            return item

    # 3. Check if label matches any word string in db associated with this item
    for item in all_items:
        words = item.get_words(db)
        for w in words:
            if normalize_label(w.string) == norm:
                return item

    return None
