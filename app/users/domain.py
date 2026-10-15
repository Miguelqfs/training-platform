from dataclasses import dataclass, field
from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


@dataclass(frozen=True)
class UserRegistration:
    username: str
    email: str
    role: UserRole
    password: str = field(repr=False)


@dataclass(frozen=True)
class NewUser:
    username: str
    email: str
    role: UserRole
    password_hash: str = field(repr=False)


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


class InvalidLoginError(InvalidCredentialsError):
    pass


class InvalidPasswordError(InvalidCredentialsError):
    pass


class PersistenceError(Exception):
    pass
