"""Enregistrement des modèles de visage d'un utilisateur connecté."""
from sqlalchemy.orm import Session

from app import face as face_mod
from app.config import settings
from app.errors import ApiError
from app.models import FaceTemplate, User


def enroll(db: Session, user: User, image: bytes, engine: face_mod.FaceEngine) -> FaceTemplate:
    if len(user.face_templates) >= settings.face_max_templates:
        raise ApiError(
            409, "FACE_LIMIT_REACHED",
            f"At most {settings.face_max_templates} face samples can be enrolled; delete them first",
        )
    vector = engine.embed(image)

    # Les échantillons suivants doivent correspondre au visage déjà enregistré.
    existing = [
        v for v in (face_mod.decrypt_embedding(t.embedding) for t in user.face_templates) if v is not None
    ]
    if existing and face_mod.best_match(vector, existing) < settings.face_match_threshold:
        raise ApiError(422, "FACE_MISMATCH", "This face does not match the face already enrolled")

    template = FaceTemplate(embedding=face_mod.encrypt_embedding(vector), model=engine.model_name)
    user.face_templates.append(template)
    db.commit()
    return template


def delete_all(db: Session, user: User) -> None:
    user.face_templates.clear()
    db.commit()
