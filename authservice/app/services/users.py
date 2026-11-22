"""Administration des comptes et création de l'admin initial."""
import logging
import math
import uuid

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError
from app.models import FaceTemplate, Role, User, UserRole, UserStatus
from app.schemas import Page, PageInfo, UserResponse
from app.services.auth import create_user, revoke_all_refresh_tokens

log = logging.getLogger("auth-service.users")


def list_users(
    db: Session, role: Role | None, status: UserStatus | None, q: str | None, page: int, size: int
) -> Page[UserResponse]:
    query = select(User)
    if role:
        query = query.where(User.id.in_(select(UserRole.user_id).where(UserRole.role == role)))
    if status:
        query = query.where(User.status == status)
    if q:
        query = query.where(User.email.contains(q.lower(), autoescape=True))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    users = db.scalars(
        query.order_by(User.created_at.desc(), User.id).offset(page * size).limit(size)
    ).all()
    return Page[UserResponse](
        content=[UserResponse.model_validate(u) for u in users],
        page=PageInfo(size=size, number=page, total_elements=total,
                      total_pages=math.ceil(total / size) if size else 0),
    )


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(404, "USER_NOT_FOUND", "User not found")
    return user


def admin_create_user(db: Session, email: str, password: str, roles: set[Role]) -> User:
    user = create_user(db, email, password, set(roles), verified=True)
    db.commit()
    return user


def update_user(
    db: Session, admin: User, user_id: uuid.UUID, status: UserStatus | None, roles: set[Role] | None
) -> User:
    user = get_user(db, user_id)
    if user.id == admin.id:
        if status == UserStatus.DISABLED or (roles is not None and Role.ADMIN not in roles):
            raise ApiError(409, "SELF_LOCKOUT", "You cannot disable yourself or remove your own ADMIN role")

    if status is not None:
        user.status = status
        if status == UserStatus.DISABLED:
            revoke_all_refresh_tokens(db, user.id)
        else:  # réactiver un compte lève aussi le verrouillage temporaire
            user.failed_attempts = 0
            user.locked_until = None
    if roles is not None:
        user.set_roles(set(roles))
    db.commit()
    db.refresh(user)
    return user


def count_face_templates(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).where(FaceTemplate.user_id == user_id))


def bootstrap_admin(db: Session) -> None:
    """Crée le premier ADMIN à partir de ADMIN_EMAIL / ADMIN_PASSWORD s'il n'existe pas."""
    email, password = settings.bootstrap_admin_email, settings.bootstrap_admin_password
    if not email or not password:
        return
    try:  # même validation que l'API, sinon l'admin ne pourrait jamais se connecter
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as exc:
        log.error("ADMIN_EMAIL invalide (%s) : admin initial non créé", exc)
        return
    if db.scalar(select(User).where(User.email == email)):
        return
    create_user(db, email, password, {Role.ADMIN}, verified=True)
    db.commit()
    log.info("Compte administrateur initial créé : %s", email)
