from db.connection import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.ai import AIPointsRequest, AIWordResponse
from services.interrogation import interrogate
from sqlalchemy.orm import Session

router = APIRouter()


# Appelle la prédiction et traduit les erreurs en réponses HTTP 422 ou 503.
@router.post("/ai/interrogate", response_model=AIWordResponse)
def interrogate_ai(capture: AIPointsRequest, db: Session = Depends(get_db)):
    try:
        return interrogate(capture, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
