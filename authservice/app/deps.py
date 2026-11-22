import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError
from app.models import Role, User, UserStatus
from app.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


@dataclass(frozen=True)
class ClientInfo:
    ip: str | None
    user_agent: str | None


def client_info(request: Request) -> ClientInfo:
    # Derrière la gateway, l'IP du client arrive dans X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
    return ClientInfo(ip=ip, user_agent=request.headers.get("user-agent"))


Client = Annotated[ClientInfo, Depends(client_info)]


def current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """La gateway laisse passer /api/auth/** sans vérifier le JWT : le service le vérifie lui-même."""
    if credentials is None:
        raise ApiError(401, "TOKEN_MISSING", "A Bearer access token is required", _UNAUTHORIZED)
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise ApiError(401, "TOKEN_INVALID", "The access token is invalid or expired", _UNAUTHORIZED)
    user = db.get(User, _uuid(claims["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise ApiError(401, "TOKEN_INVALID", "The account no longer exists or is disabled", _UNAUTHORIZED)
    return user


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise ApiError(401, "TOKEN_INVALID", "The access token is invalid or expired", _UNAUTHORIZED)


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: Role):
    def checker(user: CurrentUser) -> User:
        if not set(user.roles) & set(roles):
            raise ApiError(403, "FORBIDDEN", "You do not have the required role")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
