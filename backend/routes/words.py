from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Word
from schemas.catalog import WordDetail, WordListItem


router = APIRouter()


# Renvoie les mots du catalogue, triés par identifiant.
@router.get("/words", response_model=list[WordListItem])
async def list_words(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    return db.query(Word).order_by(Word.id).all()


# Renvoie un mot par son identifiant, ou une erreur 404.
@router.get("/words/{word_id}", response_model=WordDetail)
async def get_word(
    word_id: int,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    word = db.get(Word, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    return word
