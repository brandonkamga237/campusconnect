"""Mots de passe (argon2id), JWT d'accès (HS256) et jetons opaques (refresh, email)."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings
from app.db import utcnow

_hasher = PasswordHasher()
# Hash factice : vérifié quand l'email est inconnu pour que la réponse prenne le même temps.
_DUMMY_HASH = _hasher.hash("timing-equaliser")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def new_opaque_token() -> str:
    """Jeton aléatoire de 256 bits, transmis au client ; seul son hash est stocké."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, email: str, roles: list[str]) -> tuple[str, int]:
    now = utcnow()
    expires_in = settings.access_token_minutes * 60
    claims = {
        "iss": settings.jwt_issuer,
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256"), expires_in


def decode_access_token(token: str) -> dict:
    """Lève jwt.InvalidTokenError si le token est invalide, expiré ou d'un autre émetteur."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "sub", "iss"]},
    )


def expiry(**delta) -> datetime:
    return utcnow() + timedelta(**delta)
