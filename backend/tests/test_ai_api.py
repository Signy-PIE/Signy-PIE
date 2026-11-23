from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.prediction import LandmarkWordPredictor, PredictionResult
from db.connection import Base, get_db
from main import app
from services.prediction import predictor
from db.models import Word
from services.preprocessing import pretraiter_points


# Construit une capture de test avec une main absente et des épaules exploitables.
def capture():
    points = np.random.default_rng(7).uniform(0.2, 0.8, (12, 96, 3)).astype(np.float32)
    points[:, 53, :2] = [0.3, 0.4]
    points[:, 54, :2] = [0.7, 0.4]
    valid = np.ones((12, 96), dtype=bool)
    valid[:, 21:42] = False
    points[:, 21:42] = 0
    return {"points": points.tolist(), "valid": valid.tolist(), "fps": 25,
            "expected_word": "Bonjour"}


class AIAPITests(unittest.TestCase):
    # Prépare la base en mémoire et le client API partagés par les tests IA.
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                   poolclass=StaticPool)
        Base.metadata.create_all(cls.engine)
        with Session(cls.engine) as db:
            db.add_all([Word(id=1, string="Bonjour"),
                        Word(id=2, string="Merci")])
            db.commit()

        # Fournit une session de la base en mémoire à la place de la base réelle.
        def test_db():
            with Session(cls.engine) as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        cls.client = TestClient(app)

    # Ferme le client et libère la base et les dépendances de test.
    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()

    # Vérifie que la route de santé charge le vrai modèle et annonce ses 78 classes.
    def test_health_loads_real_model(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["classes"], 78)

    # Vérifie la forme du tenseur et le masquage des caractéristiques de la main absente.
    def test_preprocessing_preserves_missing_hand_masks(self):
        data = capture()
        data.pop("expected_word")
        tensor = pretraiter_points(**data)
        self.assertEqual(tensor.shape, (1, 90, 350))
        self.assertEqual(tensor.dtype, np.float32)
        self.assertTrue(np.isfinite(tensor).all())
        self.assertTrue(np.isin(tensor[..., 175:], [0, 1]).all())
        self.assertTrue((tensor[0, :, 42:84] == 0).all())
        self.assertTrue((tensor[0, :, 175 + 42:175 + 84] == 0).all())

    # Vérifie une prédiction réelle via l’API et la cohérence de la validation.
    def test_real_inference_via_api(self):
        response = self.client.post("/ai/interrogate", json=capture())
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertIn(result["label"], predictor.labels)
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 1)
        self.assertEqual(result["is_valid"], result["label"] == "bonjour")

    # Vérifie le format des mots et l’absence des anciennes routes vidéo.
    def test_words_do_not_require_reference_videos(self):
        response = self.client.get("/words")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": 1, "string": "Bonjour"},
                                           {"id": 2, "string": "Merci"}])
        for path in ("/videos", "/videos/1", "/video/1"):
            self.assertEqual(self.client.get(path).status_code, 404)

    # Vérifie qu’un signe Bonjour ne valide pas le mot Merci.
    def test_bonjour_does_not_validate_merci(self):
        data = capture() | {"expected_word": "Merci"}
        with patch.object(predictor, "predict", return_value=PredictionResult("bonjour", 0.9)):
            response = self.client.post("/ai/interrogate", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_valid"])
        self.assertEqual(response.json()["matched_words"], ["Bonjour"])

    # Vérifie que les accents, espaces et majuscules n’empêchent pas la comparaison.
    def test_accents_are_normalized(self):
        data = capture() | {"expected_word": " ÂGE "}
        with patch.object(predictor, "predict", return_value=PredictionResult("age", 0.9)):
            response = self.client.post("/ai/interrogate", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_valid"])

    # Vérifie que les captures invalides et les mots non reconnus sont refusés.
    def test_rejects_invalid_captures(self):
        for case in ("no_hands", "no_shoulders", "shape", "fps", "short", "mask", "word"):
            with self.subTest(case=case):
                data = capture()
                if case == "no_hands":
                    data["valid"] = [[False] * 96 for _ in data["valid"]]
                elif case == "no_shoulders":
                    for mask in data["valid"]:
                        mask[53] = mask[54] = False
                elif case == "shape":
                    data["points"][0].pop()
                elif case == "fps":
                    data["fps"] = 0
                elif case == "short":
                    data["points"] = data["points"][:4]
                    data["valid"] = data["valid"][:4]
                elif case == "mask":
                    data["valid"][0][0] = 1
                elif case == "word":
                    data["expected_word"] = "Coiffeur"
                response = self.client.post("/ai/interrogate", json=data)
                self.assertEqual(response.status_code, 422, response.text)

    # Vérifie qu’un modèle absent provoque une erreur 503 sur les routes concernées.
    def test_missing_model_returns_503(self):
        missing = LandmarkWordPredictor()
        missing.model_path = Path(__file__).with_name("absent.onnx")
        with patch("services.prediction.predictor", missing):
            self.assertEqual(self.client.get("/health").status_code, 503)
            self.assertEqual(self.client.post("/ai/interrogate", json=capture()).status_code, 503)


if __name__ == "__main__":
    unittest.main()
