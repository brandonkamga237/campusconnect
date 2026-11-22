import uuid
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)
from pydantic.alias_generators import to_camel

from app.models import Role, UserStatus

T = TypeVar("T")

Email = Annotated[EmailStr, AfterValidator(str.lower)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class ApiModel(BaseModel):
    """JSON en camelCase, comme les services Spring."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# --- requêtes -------------------------------------------------------------------------------

class RegisterRequest(ApiModel):
    email: Email
    password: Password


class LoginRequest(ApiModel):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=1, max_length=256)


class TokenRequest(ApiModel):
    token: str = Field(min_length=1, max_length=256)


class EmailRequest(ApiModel):
    email: Email


class PasswordResetRequest(ApiModel):
    token: str = Field(min_length=1, max_length=256)
    new_password: Password


class ChangePasswordRequest(ApiModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password


class CreateUserRequest(ApiModel):
    email: Email
    password: Password
    roles: set[Role] = Field(min_length=1)


class UpdateUserRequest(ApiModel):
    status: UserStatus | None = None
    roles: set[Role] | None = Field(default=None, min_length=1)


# --- réponses -------------------------------------------------------------------------------

class UserSummary(ApiModel):
    id: uuid.UUID
    email: str
    roles: list[str]


class UserResponse(UserSummary):
    status: str
    email_verified: bool
    locked_until: datetime | None
    last_login_at: datetime | None
    created_at: datetime


class MeResponse(UserResponse):
    face_enrolled: bool
    face_templates: int


class TokenResponse(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserSummary


class FaceTemplateResponse(ApiModel):
    id: uuid.UUID
    model: str
    created_at: datetime


class PageInfo(ApiModel):
    size: int
    number: int
    total_elements: int
    total_pages: int


class Page(ApiModel, Generic[T]):
    """Même forme que PagedModel de Spring Data."""

    content: list[T]
    page: PageInfo
