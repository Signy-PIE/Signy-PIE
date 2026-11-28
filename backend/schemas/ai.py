from typing import List, Optional

from pydantic import BaseModel, Field, FiniteFloat, StrictBool


class AIPointsRequest(BaseModel):
    points: List[List[tuple[FiniteFloat, FiniteFloat, FiniteFloat]]] = Field(min_length=5, max_length=1800)
    valid: List[List[StrictBool]]
    fps: FiniteFloat = Field(gt=0)
    expected_word: str = Field(min_length=1, max_length=100)


class AIWordResponse(BaseModel):
    word: str
    confidence: Optional[float] = None
    label: str
    true_label: Optional[str] = None
    matched_word_ids: List[int] = []
    matched_words: List[str] = []
    is_valid: bool = True
    tested_word: Optional[str] = None
    message: Optional[str] = None
