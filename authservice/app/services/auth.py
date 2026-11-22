"""Inscription, connexion (mot de passe / visage), jetons et verrouillage de compte."""
import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import face as face_mod
from app.config import settings
from app.db import utcnow
from app.deps import ClientInfo
from app.errors import ApiError
from app.models import (
    EmailVerificationToken,
    LoginEvent,
    LoginMethod,
    PasswordResetToken,
    RefreshToken,
    Role,
    User,
    UserStatus,
)
from app.schemas import TokenResponse, UserSummary
from app.security import (
    create_access_token,
    expiry,
    hash_password,
    hash_token,
    new_opaque_token,
    verify_password,
)

def _bad_credentials() -> ApiError:
    return ApiError(401, "BAD_CREDENTIALS", "Invalid email or password")


def _face_auth_failed() -> ApiError:
    return ApiError(401, "FACE_AUTH_FAILED", "Face authentication failed")


# --- utilitaires ----------------------------------------------------------------------------

def find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, email: str, password: str, roles: set[str], verified: bool) -> User:
    if find_user(db, email):
        raise ApiError(409, "EMAIL_TAKEN", "An account already exists with this email")
    user = User(email=email.lower(), password_hash=hash_password(password), email_verified=verified)
    user.set_roles(set(roles))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:  # inscription concurrente avec le même email
        db.rollback()
        raise ApiError(409, "EMAIL_TAKEN", "An account already exists with this email")
    return user


def _record(
    db: Session,
    method: LoginMethod,
    success: bool,
    client: ClientInfo,
    user: User | None = None,
    email: str | None = None,
    reason: str | None = None,
) -> None:
    db.add(
        LoginEvent(
            user_id=user.id if user else None,
            email=(email or (user.email if user else None)),
            method=method,
            success=success,
            reason=reason,
            ip=client.ip,
            user_agent=(client.user_agent or "")[:512] or None,
        )
    )


def revoke_all_refresh_tokens(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


def _issue_tokens(db: Session, user: User) -> tuple[TokenResponse, RefreshToken]:
    raw = new_opaque_token()
    row = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=expiry(days=settings.refresh_token_days),
    )
    db.add(row)
    access, expires_in = create_access_token(user.id, user.email, user.roles)
    response = TokenResponse(
        access_token=access,
        refresh_token=raw,
        expires_in=expires_in,
        user=UserSummary(id=user.id, email=user.email, roles=user.roles),
    )
    return response, row


# --- connexion ------------------------------------------------------------------------------

def _check_not_locked(db: Session, user: User | None, method: LoginMethod, client: ClientInfo):
    now = utcnow()
    if user is not None and user.is_locked(now):
        _record(db, method, False, client, user, reason="LOCKED")
        db.commit()
        retry_after = max(1, int((user.locked_until - now).total_seconds()))
        raise ApiError(
            423, "ACCOUNT_LOCKED",
            "Too many failed attempts, the account is temporarily locked",
            {"Retry-After": str(retry_after)},
        )


def _register_failure(
    db: Session, user: User | None, email: str, method: LoginMethod, reason: str, client: ClientInfo
) -> None:
    if user is not None:
        user.failed_attempts += 1
        if user.failed_attempts >= settings.max_failed_attempts:
            user.locked_until = utcnow() + timedelta(minutes=settings.lock_minutes)
            user.failed_attempts = 0
    _record(db, method, False, client, user, email=email, reason=reason)
    db.commit()


def _complete_login(db: Session, user: User, method: LoginMethod, client: ClientInfo) -> TokenResponse:
    """Identité prouvée : vérifie l'état du compte, puis émet les jetons."""
    if user.status != UserStatus.ACTIVE:
        _record(db, method, False, client, user, reason="DISABLED")
        db.commit()
        raise ApiError(403, "ACCOUNT_DISABLED", "This account is disabled")
    if settings.require_verified_email and not user.email_verified:
        _record(db, method, False, client, user, reason="EMAIL_NOT_VERIFIED")
        db.commit()
        raise ApiError(403, "EMAIL_NOT_VERIFIED", "Verify your email address before logging in")

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    tokens, _ = _issue_tokens(db, user)
    _record(db, method, True, client, user)
    db.commit()
    return tokens


def login_with_password(db: Session, email: str, password: str, client: ClientInfo) -> TokenResponse:
    user = find_user(db, email)
    _check_not_locked(db, user, LoginMethod.PASSWORD, client)
    # verify_password tourne même si l'email est inconnu : même temps de réponse.
    if not verify_password(password, user.password_hash if user else None):
        reason = "BAD_CREDENTIALS" if user else "UNKNOWN_EMAIL"
        _register_failure(db, user, email, LoginMethod.PASSWORD, reason, client)
        raise _bad_credentials()
    return _complete_login(db, user, LoginMethod.PASSWORD, client)


def login_with_face(
    db: Session, email: str, image: bytes, client: ClientInfo, engine: face_mod.FaceEngine
) -> TokenResponse:
    probe = engine.embed(image)  # 422 si l'image ne contient pas exactement un visage
    user = find_user(db, email)
    _check_not_locked(db, user, LoginMethod.FACE, client)

    templates = [] if user is None else [
        v for v in (face_mod.decrypt_embedding(t.embedding) for t in user.face_templates) if v is not None
    ]
    if not templates:
        reason = "UNKNOWN_EMAIL" if user is None else "FACE_NOT_ENROLLED"
        _record(db, LoginMethod.FACE, False, client, user, email=email, reason=reason)
        db.commit()
        raise _face_auth_failed()

    if face_mod.best_match(probe, templates) < settings.face_match_threshold:
        _register_failure(db, user, email, LoginMethod.FACE, "FACE_MISMATCH", client)
        raise _face_auth_failed()
    return _complete_login(db, user, LoginMethod.FACE, client)


# --- refresh / logout -----------------------------------------------------------------------

def refresh(db: Session, raw_token: str, client: ClientInfo) -> TokenResponse:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if row is None:
        raise ApiError(401, "TOKEN_INVALID", "The refresh token is invalid")

    user = row.user
    if row.revoked_at is not None and row.replaced_by is None:
        # Révoqué par logout, changement de mot de passe ou désactivation : simple refus.
        raise ApiError(401, "TOKEN_REVOKED", "The refresh token has been revoked")
    if row.revoked_at is not None:
        # Un jeton déjà échangé revient : il a probablement été volé. On coupe toutes les sessions.
        revoke_all_refresh_tokens(db, user.id)
        _record(db, LoginMethod.REFRESH, False, client, user, reason="TOKEN_REUSE")
        db.commit()
        raise ApiError(401, "TOKEN_REUSED", "The refresh token was already used; all sessions were revoked")
    if row.expires_at <= utcnow():
        raise ApiError(401, "TOKEN_EXPIRED", "The refresh token has expired")
    if user.status != UserStatus.ACTIVE:
        raise ApiError(401, "ACCOUNT_DISABLED", "This account is disabled")

    tokens, new_row = _issue_tokens(db, user)
    db.flush()  # le nouveau jeton doit exister en base avant que l'ancien pointe dessus (clé étrangère)
    row.revoked_at = utcnow()
    row.replaced_by = new_row.id
    _record(db, LoginMethod.REFRESH, True, client, user)
    db.commit()
    return tokens


def logout(db: Session, raw_token: str) -> None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if row is not None and row.revoked_at is None:
        row.revoked_at = utcnow()
        db.commit()


# --- jetons envoyés par email ---------------------------------------------------------------

def _issue_one_time_token(db: Session, model, user: User, **ttl) -> str:
    # Un seul jeton valide à la fois : les précédents non utilisés sont supprimés.
    for old in db.scalars(select(model).where(model.user_id == user.id, model.used_at.is_(None))):
        db.delete(old)
    raw = new_opaque_token()
    db.add(model(user_id=user.id, token_hash=hash_token(raw), expires_at=expiry(**ttl)))
    return raw


def _consume_one_time_token(db: Session, model, raw: str):
    row = db.scalar(select(model).where(model.token_hash == hash_token(raw)))
    if row is None or row.used_at is not None or row.expires_at <= utcnow():
        raise ApiError(400, "TOKEN_INVALID", "The token is invalid, expired or already used")
    row.used_at = utcnow()
    return row


def register(db: Session, email: str, password: str) -> tuple[User, str]:
    user = create_user(db, email, password, {Role.STUDENT}, verified=False)
    token = _issue_one_time_token(
        db, EmailVerificationToken, user, hours=settings.email_verification_hours
    )
    db.commit()
    return user, token


def verify_email(db: Session, raw: str) -> None:
    row = _consume_one_time_token(db, EmailVerificationToken, raw)
    row.user.email_verified = True
    db.commit()


def resend_verification(db: Session, email: str) -> str | None:
    user = find_user(db, email)
    if user is None or user.email_verified:
        return None
    token = _issue_one_time_token(
        db, EmailVerificationToken, user, hours=settings.email_verification_hours
    )
    db.commit()
    return token


def forgot_password(db: Session, email: str) -> str | None:
    user = find_user(db, email)
    if user is None or user.status != UserStatus.ACTIVE:
        return None
    token = _issue_one_time_token(
        db, PasswordResetToken, user, minutes=settings.password_reset_minutes
    )
    db.commit()
    return token


def _set_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    user.failed_attempts = 0
    user.locked_until = None
    revoke_all_refresh_tokens(db, user.id)  # déconnecte toutes les sessions


def reset_password(db: Session, raw: str, new_password: str) -> None:
    row = _consume_one_time_token(db, PasswordResetToken, raw)
    _set_password(db, row.user, new_password)
    db.commit()


def change_password(db: Session, user: User, current: str, new_password: str) -> None:
    if not verify_password(current, user.password_hash):
        raise ApiError(400, "INVALID_CURRENT_PASSWORD", "The current password is incorrect")
    _set_password(db, user, new_password)
    db.commit()
