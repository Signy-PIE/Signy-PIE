from typing import List

from pydantic import BaseModel, ConfigDict


class WordListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    string: str


class WordDetail(WordListItem):
    pass


class LessonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    words: List[WordDetail]


class LessonDetail(LessonListItem):
    pass


class WordCorespondanceListItem(BaseModel):
    id: int
    label: str
    words: List[int]


class WordCorespondanceDetail(BaseModel):
    id: int
    label: str
    words: List[int]
    matched_words: List[WordDetail] = []
