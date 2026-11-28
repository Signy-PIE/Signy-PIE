from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from schemas.catalog import LessonListItem


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    email: str
    premium: bool
    creation_date: datetime
    lessons_done: List[LessonListItem]


class UserDetail(UserListItem):
    pass
