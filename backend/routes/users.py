from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.connection import get_db
from db.models import User
from schemas.users import UserDetail, UserListItem


router = APIRouter()


# Renvoie les utilisateurs avec leurs leçons terminées.
@router.get("/users", response_model=list[UserListItem])
async def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


# Renvoie un utilisateur par son identifiant, ou une erreur 404.
@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
