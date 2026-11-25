from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import RLock

from app.accesses.domain import OPERATIONS, AccessEvent, interval
from app.accesses.ports import AccessEventRepository as AccessEventRepository
from app.storage import sqlite_connection
from app.users.domain import PersistenceError

_OPERATION_CHECK = f"CHECK (operation IN ({', '.join(map(repr, OPERATIONS))}))"


def _create_access_events_table(db: sqlite3.Connection, table: str) -> None:
    db.execute(f"""CREATE TABLE {table} (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        operation TEXT NOT NULL {_OPERATION_CHECK},
        occurred_at TEXT NOT NULL
    )""")


def _initialize_access_events(db: sqlite3.Connection) -> None:
    # Start before inspecting the schema so opening the same database serializes migration.
    db.execute("BEGIN IMMEDIATE")
    existing = db.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = 'access_events'"
    ).fetchone()
    if existing is None:
        _create_access_events_table(db, "access_events")
    elif _OPERATION_CHECK not in existing[0]:
        _create_access_events_table(db, "access_events_new")
        db.execute(
            """INSERT INTO access_events_new (id, user_id, operation, occurred_at)
               SELECT id, user_id, operation, occurred_at FROM access_events"""
        )
        db.execute("DROP TABLE access_events")
        db.execute("ALTER TABLE access_events_new RENAME TO access_events")
    db.execute(
        "CREATE INDEX IF NOT EXISTS access_events_occurred_at ON access_events(occurred_at)"
    )


class MemoryAccessEventRepository:
    def __init__(self, lock: RLock | None = None) -> None:
        self._events: list[AccessEvent] = []
        self._lock = lock if lock is not None else RLock()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            events = self._events.copy()
            try:
                yield
            except BaseException:
                self._events = events
                raise

    def add(self, event: AccessEvent) -> None:
        with self._lock:
            self._events.append(event)

    def list_between(self, start: datetime, end: datetime) -> list[AccessEvent]:
        start, end = interval(start, end)
        with self._lock:
            return sorted(
                (event for event in self._events if start <= event.occurred_at < end),
                key=lambda event: event.occurred_at,
            )


class SQLiteAccessEventRepository:
    def __init__(
        self, path: Path, connection: sqlite3.Connection | None = None
    ) -> None:
        self._path, self._connection = path, connection
        if connection is None:
            try:
                with sqlite_connection(path) as db:
                    _initialize_access_events(db)
            except sqlite3.Error as error:
                raise PersistenceError(
                    "Não foi possível inicializar eventos"
                ) from error

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        if self._connection is not None:
            yield self._connection
        else:
            with sqlite_connection(self._path) as connection:
                yield connection

    def add(self, event: AccessEvent) -> None:
        try:
            with self._db() as db:
                db.execute(
                    "INSERT INTO access_events (user_id, operation, occurred_at) VALUES (?, ?, ?)",
                    (
                        str(event.user_id),
                        event.operation,
                        event.occurred_at.isoformat(timespec="microseconds"),
                    ),
                )
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível armazenar evento") from error

    def list_between(self, start: datetime, end: datetime) -> list[AccessEvent]:
        start, end = interval(start, end)
        try:
            with self._db() as db:
                rows = db.execute(
                    "SELECT user_id, operation, occurred_at FROM access_events WHERE occurred_at >= ? AND occurred_at < ? ORDER BY occurred_at, id",
                    (
                        start.isoformat(timespec="microseconds"),
                        end.isoformat(timespec="microseconds"),
                    ),
                ).fetchall()
            return [
                AccessEvent(user_id, operation, datetime.fromisoformat(occurred_at))
                for user_id, operation, occurred_at in rows
            ]
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível consultar eventos") from error
