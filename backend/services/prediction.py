from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import os

import numpy as np

from services.preprocessing import charger_metadata, pretraiter_points

BASE = Path(__file__).resolve().parents[1] / "assets"


@dataclass
class PredictionResult:
    word: str
    confidence: float


class LandmarkWordPredictor:
    # Configure les chemins du modèle et prépare son chargement différé.
    def __init__(self):
        self.model_path = Path(os.getenv("AI_MODEL_PATH", BASE / "modele_tcn.onnx"))
        self.metadata_path = Path(os.getenv("AI_METADATA_PATH", self.model_path.with_name("metadata.json")))
        self.session = None
        self.metadata = None
        self.labels = []
        self.lock = Lock()

    # Charge et vérifie une seule fois le modèle ONNX et ses métadonnées.
    def load(self):
        with self.lock:
            if self.session is not None:
                return
            try:
                import onnxruntime as ort

                metadata = charger_metadata(self.metadata_path)
                labels = metadata["labels"]
                if (not isinstance(labels, list) or not labels
                        or not all(isinstance(label, str) and label.strip() for label in labels)
                        or len(labels) != len(set(labels))):
                    raise ValueError("Labels invalides.")
                options = ort.SessionOptions()
                options.intra_op_num_threads = 1
                options.inter_op_num_threads = 1
                session = ort.InferenceSession(str(self.model_path), options,
                                               providers=["CPUExecutionProvider"])
                if (len(session.get_inputs()) != 1
                        or session.get_inputs()[0].shape != metadata["entree"]
                        or session.get_inputs()[0].type != "tensor(float)"
                        or session.get_outputs()[0].shape != [1, len(labels)]):
                    raise ValueError("Le modèle ne correspond pas aux métadonnées.")
            except Exception as exc:
                raise RuntimeError("Le modèle IA est indisponible.") from exc
            self.metadata, self.labels, self.session = metadata, labels, session

    # Prétraite les points, exécute le modèle et renvoie le signe au score le plus élevé.
    def predict(self, points, valid, fps):
        self.load()
        tensor = pretraiter_points(points, valid, fps, self.metadata)
        try:
            logits = self.session.run(None, {self.session.get_inputs()[0].name: tensor})[0][0]
            if not np.isfinite(logits).all():
                raise ValueError("Scores non finis.")
            probabilities = np.exp(logits - np.max(logits))
            probabilities /= probabilities.sum()
        except Exception as exc:
            raise RuntimeError("La prédiction IA a échoué.") from exc
        index = int(probabilities.argmax())
        return PredictionResult(self.labels[index], float(probabilities[index]))


predictor = LandmarkWordPredictor()
