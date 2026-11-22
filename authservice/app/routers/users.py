"""Administration des comptes (rôle ADMIN)."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.deps import AdminUser, DbSession
from app.models import Role, UserStatus
from app.schemas import CreateUserRequest, Page, UpdateUserRequest, UserResponse
from app.services import users as user_service

router = APIRouter(prefix="/api/auth/users", tags=["Administration des comptes"])


@router.get("", response_model=Page[UserResponse])
def list_users(
    _: AdminUser,
    db: DbSession,
    role: Role | None = None,
    status_: Annotated[UserStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=100, description="Recherche dans l'email")] = None,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return user_service.list_users(db, role, status_, q, page, size)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(body: CreateUserRequest, _: AdminUser, db: DbSession):
    """Crée un compte déjà vérifié (enseignants, administrateurs…)."""
    return user_service.admin_create_user(db, body.email, body.password, body.roles)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, _: AdminUser, db: DbSession):
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, body: UpdateUserRequest, admin: AdminUser, db: DbSession):
    """Change le statut et/ou les rôles. Passer à ACTIVE lève aussi un verrouillage temporaire."""
    return user_service.update_user(db, admin, user_id, body.status, body.roles)
