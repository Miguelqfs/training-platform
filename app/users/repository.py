import sqlite3
from pathlib import Path
from threading import Lock
from typing import Protocol

from app.storage import sqlite_connection
from app.users.domain import (
    DuplicateUserError,
    NewUser,
    PersistenceError,
    User,
    UserRole,
)


class UserRepository(Protocol):
    def add(self, data: NewUser) -> User: ...
    def list_users(self) -> list[User]: ...
    def get_by_id(self, user_id: int) -> User | None: ...
    def count(self) -> int: ...


class MemoryUserRepository:
    def __init__(self) -> None:
        self._users: list[User] = []
        self._lock = Lock()

    def add(self, data: NewUser) -> User:
        with self._lock:
            if any(
                user.username.casefold() == data.username.casefold()
                or user.email.casefold() == data.email.casefold()
                for user in self._users
            ):
                raise DuplicateUserError("Usuário ou e-mail já cadastrado")
            user = User(
                id=len(self._users) + 1,
                username=data.username,
                email=data.email,
                role=data.role,
                password_hash=data.password_hash,
            )
            self._users.append(user)
            return user

    def list_users(self) -> list[User]:
        with self._lock:
            return list(self._users)

    def get_by_id(self, user_id: int) -> User | None:
        with self._lock:
            return next((user for user in self._users if user.id == user_id), None)

    def count(self) -> int:
        with self._lock:
            return len(self._users)


class SQLiteUserRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        try:
            with sqlite_connection(self._path) as connection:
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

    def add(self, data: NewUser) -> User:
        try:
            with sqlite_connection(self._path) as connection:
                cursor = connection.execute(
                    "INSERT INTO users (username, username_key, email, email_key, role, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        data.username,
                        data.username.casefold(),
                        data.email,
                        data.email.casefold(),
                        data.role.value,
                        data.password_hash,
                    ),
                )
                assert cursor.lastrowid is not None
                return User(
                    id=cursor.lastrowid,
                    username=data.username,
                    email=data.email,
                    role=data.role,
                    password_hash=data.password_hash,
                )
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
            with sqlite_connection(self._path) as connection:
                rows = connection.execute(
                    "SELECT id, username, email, role, password_hash FROM users ORDER BY id"
                ).fetchall()
            return [
                User(id, username, email, UserRole(role), password_hash)
                for id, username, email, role, password_hash in rows
            ]
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível listar os usuários") from error

    def get_by_id(self, user_id: int) -> User | None:
        try:
            with sqlite_connection(self._path) as connection:
                # Texto decimal evita overflow do driver para IDs positivos muito grandes.
                row = connection.execute(
                    "SELECT id, username, email, role, password_hash FROM users WHERE id = ?",
                    (str(user_id),),
                ).fetchone()
            if row is None:
                return None
            return User(row[0], row[1], row[2], UserRole(row[3]), row[4])
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível consultar o usuário") from error

    def count(self) -> int:
        try:
            with sqlite_connection(self._path) as connection:
                return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível contar os usuários") from error
