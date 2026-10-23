import os
from pathlib import Path

from app.users.repository import (
    MemoryUserRepository,
    SQLiteUserRepository,
    UserRepository,
)


def resolve_storage(
    storage: str | None = None, database_path: Path | None = None
) -> tuple[str, Path]:
    selected = storage if storage is not None else os.getenv("USER_STORAGE", "memory")
    if selected not in ("memory", "sqlite"):
        raise ValueError("USER_STORAGE deve ser memory ou sqlite")
    path = (
        database_path
        if database_path is not None
        else Path(os.getenv("USER_DATABASE", "users.sqlite3"))
    )
    return selected, path


def create_user_repository(
    storage: str | None = None, database_path: Path | None = None
) -> UserRepository:
    storage, path = resolve_storage(storage, database_path)
    if storage == "memory":
        return MemoryUserRepository()
    return SQLiteUserRepository(path)
