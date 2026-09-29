from dataclasses import dataclass
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    id: int
    username: str
    email: str
    role: UserRole


class DuplicateUserError(Exception):
    pass
