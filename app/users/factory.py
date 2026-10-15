import os
from pathlib import Path

from app.users.repository import (
    MemoryUserRepository,
    SQLiteUserRepository,
    UserRepository,
)


def create_user_repository(
    storage: str | None = None, database_path: Path | None = None
) -> UserRepository:
    storage = storage if storage is not None else os.getenv("USER_STORAGE", "memory")
    if storage == "memory":
        return MemoryUserRepository()
    if storage == "sqlite":
        path = (
            database_path
            if database_path is not None
            else Path(os.getenv("USER_DATABASE", "users.sqlite3"))
        )
        return SQLiteUserRepository(path)
    raise ValueError("USER_STORAGE deve ser memory ou sqlite")
