from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import Lesson
from schemas.catalog import LessonDetail, LessonListItem


router = APIRouter()


# Renvoie les leçons et leurs mots, triées par identifiant.
@router.get("/lessons", response_model=list[LessonListItem])
async def list_lessons(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    return db.query(Lesson).order_by(Lesson.id).all()


# Renvoie une leçon et ses mots, ou une erreur 404.
@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: int,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return lesson
