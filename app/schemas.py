from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from app.users.domain import UserRole


class UserFields(BaseModel):
    username: str = Field(min_length=1, max_length=12)
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
