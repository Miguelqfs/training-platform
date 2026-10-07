from dataclasses import dataclass, field
from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    id: int
    username: str
    email: str
    role: UserRole
    password_hash: str = field(repr=False)


class DuplicateUserError(Exception):
    pass


class InvalidCredentialsError(ValueError):
    pass


class PersistenceError(Exception):
    pass
