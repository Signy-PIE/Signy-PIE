from typing import Dict

from fastapi import APIRouter, HTTPException

from services import prediction


router = APIRouter()


# Confirme que l’API est accessible.
@router.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Signy PIE API is running"}


# Vérifie le chargement du modèle et renvoie son état.
@router.get("/health")
def health():
    try:
        prediction.predictor.load()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "model": prediction.predictor.model_path.name, "classes": len(prediction.predictor.labels)}
