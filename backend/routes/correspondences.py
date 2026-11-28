from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import WordCorespondance
from schemas.catalog import WordCorespondanceDetail
from services.correspondences import find_corespondance_by_label
from utils.serializers import serialize_corespondance


router = APIRouter()


# Liste les correspondances entre signes et mots via les deux URL existantes.
@router.get("/word-corespondance", response_model=list[WordCorespondanceDetail])
@router.get("/word-correspondances", response_model=list[WordCorespondanceDetail])
async def list_word_corespondances(db: Session = Depends(get_db)):
    """List all sign-to-words correspondances."""
    items = db.query(WordCorespondance).order_by(WordCorespondance.id).all()
    return [serialize_corespondance(item, db) for item in items]


# Renvoie une correspondance par identifiant via les deux URL, ou une erreur 404.
@router.get("/word-corespondance/{corespondance_id}", response_model=WordCorespondanceDetail)
@router.get("/word-correspondances/{corespondance_id}", response_model=WordCorespondanceDetail)
async def get_word_corespondance(
    corespondance_id: int,
    db: Session = Depends(get_db),
):
    """Get a single sign correspondance by ID."""
    item = db.get(WordCorespondance, corespondance_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Word correspondance not found")
    return serialize_corespondance(item, db)


# Recherche une correspondance par libellé ou alias via les deux URL existantes.
@router.get("/word-corespondance/by-label/{label}", response_model=WordCorespondanceDetail)
@router.get("/word-correspondances/by-label/{label}", response_model=WordCorespondanceDetail)
async def get_word_corespondance_by_label(
    label: str,
    db: Session = Depends(get_db),
):
    """Find a sign correspondance by its model label or alias."""
    item = find_corespondance_by_label(db, label)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No correspondance found for label '{label}'")
    return serialize_corespondance(item, db)
