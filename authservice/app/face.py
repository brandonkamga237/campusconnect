"""Reconnaissance faciale avec des modèles pré-entraînés exécutés par OpenCV (pas de torch/tensorflow).

- Détection : YuNet  (face_detection_yunet_2023mar.onnx)
- Embedding : SFace  (face_recognition_sface_2021dec.onnx), vecteur de 128 floats
- Comparaison : similarité cosinus ; même personne si >= seuil (0.363, valeur de référence SFace)

Les embeddings sont chiffrés (Fernet) avant d'être stockés : aucune image n'est conservée.
"""
import base64
import hashlib
import logging
import threading
from pathlib import Path

import cv2
import numpy as np
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.errors import ApiError

log = logging.getLogger("auth-service.face")

MODEL_NAME = "opencv-sface-2021dec"
DETECTOR_FILE = "face_detection_yunet_2023mar.onnx"
RECOGNIZER_FILE = "face_recognition_sface_2021dec.onnx"
MAX_SIDE = 800  # les grandes photos sont réduites avant détection


class FaceEngine:
    """Calcule l'embedding d'une photo contenant exactement un visage."""

    model_name = MODEL_NAME

    def __init__(self, model_dir: str):
        model_path = Path(model_dir)
        self._detector = cv2.FaceDetectorYN.create(
            str(model_path / DETECTOR_FILE), "", (320, 320), 0.9, 0.3, 5000
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(model_path / RECOGNIZER_FILE), "")
        self._lock = threading.Lock()  # les réseaux OpenCV ne sont pas thread-safe

    def embed(self, image_bytes: bytes) -> np.ndarray:
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ApiError(422, "INVALID_IMAGE", "The file is not a readable JPEG or PNG image")
        h, w = image.shape[:2]
        scale = MAX_SIDE / max(h, w)
        if scale < 1:
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
            h, w = image.shape[:2]

        with self._lock:
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(image)
            count = 0 if faces is None else len(faces)
            if count == 0:
                raise ApiError(422, "NO_FACE_DETECTED", "No face was detected in the image")
            if count > 1:
                raise ApiError(422, "MULTIPLE_FACES", "Exactly one face must be visible")
            aligned = self._recognizer.alignCrop(image, faces[0])
            feature = self._recognizer.feature(aligned).flatten().astype(np.float32)

        return feature / np.linalg.norm(feature)


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def best_match(probe: np.ndarray, templates: list[np.ndarray]) -> float:
    return max((similarity(probe, t) for t in templates), default=-1.0)


# --- chiffrement des embeddings -------------------------------------------------------------

def _fernet() -> Fernet:
    key = hashlib.sha256(settings.face_encryption_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_embedding(vector: np.ndarray) -> bytes:
    return _fernet().encrypt(vector.astype(np.float32).tobytes())


def decrypt_embedding(blob: bytes) -> np.ndarray | None:
    try:
        return np.frombuffer(_fernet().decrypt(blob), dtype=np.float32)
    except InvalidToken:  # clé changée : le modèle est inutilisable
        log.error("Embedding illisible : FACE_ENCRYPTION_KEY a-t-elle changé ?")
        return None


# --- instance partagée ----------------------------------------------------------------------

_engine: FaceEngine | None = None


def init_engine() -> None:
    global _engine
    try:
        _engine = FaceEngine(settings.face_model_dir)
        log.info("Modèles de visage chargés depuis %s", settings.face_model_dir)
    except cv2.error as exc:
        _engine = None
        log.warning("Reconnaissance faciale indisponible (modèles introuvables ?) : %s", exc)


def get_engine() -> FaceEngine:
    if _engine is None:
        raise ApiError(503, "FACE_UNAVAILABLE", "Face recognition is not available")
    return _engine


def engine_ready() -> bool:
    return _engine is not None
