import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Lock
from typing import Protocol

from app.users.domain import DuplicateUserError, PersistenceError, User, UserRole


class UserRepository(Protocol):
    def add(
        self, username: str, email: str, role: UserRole, password_hash: str
    ) -> User: ...
    def list_users(self) -> list[User]: ...


class MemoryUserRepository:
    def __init__(self) -> None:
        self._users: list[User] = []
        self._lock = Lock()

    def add(
        self, username: str, email: str, role: UserRole, password_hash: str
    ) -> User:
        with self._lock:
            if any(
                user.username.casefold() == username.casefold()
                or user.email.casefold() == email.casefold()
                for user in self._users
            ):
                raise DuplicateUserError("Usuário ou e-mail já cadastrado")
            user = User(len(self._users) + 1, username, email, role, password_hash)
            self._users.append(user)
            return user

    def list_users(self) -> list[User]:
        with self._lock:
            return list(self._users)


class SQLiteUserRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        try:
            with closing(sqlite3.connect(self._path)) as connection, connection:
                connection.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    username_key TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    email_key TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL CHECK (role IN ('student', 'admin')),
                    password_hash TEXT NOT NULL
                )""")
        except sqlite3.Error as error:
            raise PersistenceError(
                "Não foi possível inicializar o banco de usuários"
            ) from error

    def add(
        self, username: str, email: str, role: UserRole, password_hash: str
    ) -> User:
        try:
            with closing(sqlite3.connect(self._path)) as connection, connection:
                cursor = connection.execute(
                    "INSERT INTO users (username, username_key, email, email_key, role, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        username,
                        username.casefold(),
                        email,
                        email.casefold(),
                        role.value,
                        password_hash,
                    ),
                )
                assert cursor.lastrowid is not None
                return User(cursor.lastrowid, username, email, role, password_hash)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode in (
                sqlite3.SQLITE_CONSTRAINT_UNIQUE,
                sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY,
            ):
                raise DuplicateUserError("Usuário ou e-mail já cadastrado") from error
            raise PersistenceError("Não foi possível armazenar o usuário") from error
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível armazenar o usuário") from error

    def list_users(self) -> list[User]:
        try:
            with closing(sqlite3.connect(self._path)) as connection:
                rows = connection.execute(
                    "SELECT id, username, email, role, password_hash FROM users ORDER BY id"
                ).fetchall()
            return [
                User(id, username, email, UserRole(role), password_hash)
                for id, username, email, role, password_hash in rows
            ]
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível listar os usuários") from error
