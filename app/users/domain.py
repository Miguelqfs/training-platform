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
    USER_MESSAGE = "Armazenamento de usuários indisponível"
    WORKOUT_MESSAGE = "Armazenamento de treinos indisponível"

    def __init__(self, message: str, *, public_message: str = USER_MESSAGE) -> None:
        if public_message not in (self.USER_MESSAGE, self.WORKOUT_MESSAGE):
            raise ValueError("Mensagem pública de persistência desconhecida")
        super().__init__(message)
        self.public_message = public_message
