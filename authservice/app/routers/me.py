"""Compte de l'utilisateur connecté (JWT obligatoire)."""
from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app import face as face_mod
from app.deps import CurrentUser, DbSession
from app.routers.uploads import read_image
from app.schemas import ChangePasswordRequest, FaceTemplateResponse, MeResponse, UserResponse
from app.services import auth as auth_service
from app.services import faces as face_service

router = APIRouter(prefix="/api/auth/me", tags=["Mon compte"])


@router.get("", response_model=MeResponse)
def me(user: CurrentUser):
    count = len(user.face_templates)
    return MeResponse(
        **UserResponse.model_validate(user).model_dump(), face_enrolled=count > 0, face_templates=count
    )


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    """Change le mot de passe et révoque toutes les sessions (refresh tokens)."""
    auth_service.change_password(db, user, body.current_password, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/face", response_model=list[FaceTemplateResponse])
def list_face_templates(user: CurrentUser):
    return user.face_templates


@router.post("/face", status_code=status.HTTP_201_CREATED, response_model=FaceTemplateResponse)
async def enroll_face(
    user: CurrentUser,
    db: DbSession,
    image: Annotated[UploadFile, File(description="Photo JPEG ou PNG avec un seul visage")],
):
    """Ajoute un échantillon de visage (3 maximum). Les suivants doivent correspondre au premier."""
    data = await read_image(image)
    engine = face_mod.get_engine()
    return await run_in_threadpool(face_service.enroll, db, user, data, engine)


@router.delete("/face", status_code=status.HTTP_204_NO_CONTENT)
def delete_face_templates(user: CurrentUser, db: DbSession):
    """Supprime toutes les données de visage de l'utilisateur."""
    face_service.delete_all(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
