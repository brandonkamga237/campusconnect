"""Endpoints publics : inscription, connexion, jetons, email et mot de passe oublié."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app import face as face_mod
from app import mailer
from app.deps import Client, DbSession
from app.routers.uploads import read_image
from app.schemas import (
    EmailRequest,
    LoginRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(body: RegisterRequest, db: DbSession, background: BackgroundTasks):
    """Crée un compte STUDENT et envoie l'email de vérification."""
    user, token = auth_service.register(db, body.email, body.password)
    background.add_task(mailer.send_mail, *mailer.verification_email(user.email, token))
    return user


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(body: TokenRequest, db: DbSession):
    auth_service.verify_email(db, body.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
def resend_verification(body: EmailRequest, db: DbSession, background: BackgroundTasks):
    """Répond toujours 202 pour ne pas révéler si l'email existe."""
    token = auth_service.resend_verification(db, body.email)
    if token:
        background.add_task(mailer.send_mail, *mailer.verification_email(body.email, token))
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession, client: Client):
    return auth_service.login_with_password(db, body.email, body.password, client)


@router.post("/login/face", response_model=TokenResponse)
async def login_with_face(
    db: DbSession,
    client: Client,
    email: Annotated[str, Form(max_length=254)],
    image: Annotated[UploadFile, File(description="Photo JPEG ou PNG avec un seul visage")],
):
    """Connexion 1:1 : la photo est comparée aux visages enregistrés pour cet email."""
    data = await read_image(image)
    engine = face_mod.get_engine()
    return await run_in_threadpool(
        auth_service.login_with_face, db, email.strip().lower(), data, client, engine
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DbSession, client: Client):
    """Échange un refresh token contre une nouvelle paire ; l'ancien devient inutilisable."""
    return auth_service.refresh(db, body.refresh_token, client)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: DbSession):
    auth_service.logout(db, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: EmailRequest, db: DbSession, background: BackgroundTasks):
    """Répond toujours 202 pour ne pas révéler si l'email existe."""
    token = auth_service.forgot_password(db, body.email)
    if token:
        background.add_task(mailer.send_mail, *mailer.password_reset_email(body.email, token))
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: PasswordResetRequest, db: DbSession):
    auth_service.reset_password(db, body.token, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
