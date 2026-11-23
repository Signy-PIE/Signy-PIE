from sqlalchemy.orm import Session

from db.models import Word
from schemas.ai import AIPointsRequest, AIWordResponse
from services import prediction
from utils.labels import normalize_label


# Compare le signe prédit au mot attendu et construit la réponse de validation.
def interrogate(capture: AIPointsRequest, db: Session) -> AIWordResponse:
    expected_word = capture.expected_word.strip()
    target = normalize_label(expected_word)
    prediction.predictor.load()
    if target not in {normalize_label(label) for label in prediction.predictor.labels}:
        raise ValueError(f"Le modèle ne reconnaît pas le mot '{expected_word}'.")
    result = prediction.predictor.predict(capture.points, capture.valid, capture.fps)

    label = result.word
    matched = [word for word in db.query(Word).all()
               if normalize_label(word.string) == normalize_label(label)]
    is_valid = normalize_label(label) == target
    message = (f"Le signe reconnu correspond à '{expected_word}'." if is_valid else
               f"Le signe reconnu est '{label}', le mot attendu est '{expected_word}'. Réessayez !")
    return AIWordResponse(
        word=label,
        confidence=result.confidence,
        label=label,
        true_label=label,
        matched_word_ids=[word.id for word in matched],
        matched_words=[word.string for word in matched] or [label],
        is_valid=is_valid,
        tested_word=expected_word,
        message=message,
    )
