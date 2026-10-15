from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from app.users.domain import UserRole
from app.users.policy import MAX_LOGIN_LENGTH, MIN_LOGIN_LENGTH


class UserFields(BaseModel):
    username: str = Field(min_length=MIN_LOGIN_LENGTH, max_length=MAX_LOGIN_LENGTH)
    email: EmailStr
    role: UserRole = UserRole.STUDENT

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UserCreate(UserFields):
    password: SecretStr


class User(UserFields):
    id: int
