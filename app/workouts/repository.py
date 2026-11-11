from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from threading import RLock

from app.storage import sqlite_connection
from app.users.domain import PersistenceError
from app.workouts.domain import (
    UserNotFoundError,
    Workout,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.ports import WorkoutRepository as WorkoutRepository


class MemoryWorkoutRepository:
    def __init__(self, lock: RLock | None = None) -> None:
        self._workouts: dict[int, Workout] = {}
        self._next_id = 1
        self._lock = lock if lock is not None else RLock()

    def add(self, data: WorkoutRegistration) -> Workout:
        with self._lock:
            workout = Workout(self._next_id, data.user_id, data.name, data.description)
            self._workouts[workout.id] = workout
            self._next_id += 1
            return workout

    def get_by_id(self, workout_id: int) -> Workout | None:
        with self._lock:
            return self._workouts.get(workout_id)

    def list_workouts(self) -> list[Workout]:
        with self._lock:
            return sorted(self._workouts.values(), key=lambda workout: workout.id)

    def update(self, workout_id: int, data: WorkoutUpdate) -> Workout | None:
        with self._lock:
            workout = self._workouts.get(workout_id)
            if workout is None:
                return None
            updated = replace(workout, name=data.name, description=data.description)
            self._workouts[workout_id] = updated
            return updated

    def delete(self, workout_id: int) -> bool:
        with self._lock:
            return self._workouts.pop(workout_id, None) is not None

    def count(self) -> int:
        with self._lock:
            return len(self._workouts)


def storage_failure() -> PersistenceError:
    return PersistenceError(
        "Não foi possível acessar os treinos",
        public_message=PersistenceError.WORKOUT_MESSAGE,
    )


class SQLiteWorkoutRepository:
    def __init__(
        self, path: Path, connection: sqlite3.Connection | None = None
    ) -> None:
        self._path = path
        self._connection = connection
        if connection is not None:
            return
        try:
            with self._db() as connection:
                connection.execute("""CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )""")
        except sqlite3.Error as error:
            raise storage_failure() from error

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        if self._connection is not None:
            yield self._connection
        else:
            with sqlite_connection(self._path) as connection:
                yield connection

    def add(self, data: WorkoutRegistration) -> Workout:
        try:
            with self._db() as connection:
                # Afinidade INTEGER do SQLite preserva IDs sem overflow do binding Python.
                cursor = connection.execute(
                    "INSERT INTO workouts (user_id, name, description) VALUES (?, ?, ?)",
                    (str(data.user_id), data.name, data.description),
                )
                assert cursor.lastrowid is not None
                return Workout(
                    cursor.lastrowid, data.user_id, data.name, data.description
                )
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                raise UserNotFoundError() from error
            raise storage_failure() from error
        except sqlite3.Error as error:
            raise storage_failure() from error

    def get_by_id(self, workout_id: int) -> Workout | None:
        try:
            with self._db() as connection:
                row = connection.execute(
                    "SELECT id, user_id, name, description FROM workouts WHERE id = ?",
                    (str(workout_id),),
                ).fetchone()
            return Workout(*row) if row is not None else None
        except sqlite3.Error as error:
            raise storage_failure() from error

    def list_workouts(self) -> list[Workout]:
        try:
            with self._db() as connection:
                rows = connection.execute(
                    "SELECT id, user_id, name, description FROM workouts ORDER BY id"
                ).fetchall()
            return [Workout(*row) for row in rows]
        except sqlite3.Error as error:
            raise storage_failure() from error

    def update(self, workout_id: int, data: WorkoutUpdate) -> Workout | None:
        try:
            with self._db() as connection:
                cursor = connection.execute(
                    "UPDATE workouts SET name = ?, description = ? WHERE id = ?",
                    (data.name, data.description, str(workout_id)),
                )
                if cursor.rowcount == 0:
                    return None
                row = connection.execute(
                    "SELECT id, user_id, name, description FROM workouts WHERE id = ?",
                    (str(workout_id),),
                ).fetchone()
                return Workout(*row)
        except sqlite3.Error as error:
            raise storage_failure() from error

    def delete(self, workout_id: int) -> bool:
        try:
            with self._db() as connection:
                return (
                    connection.execute(
                        "DELETE FROM workouts WHERE id = ?", (str(workout_id),)
                    ).rowcount
                    > 0
                )
        except sqlite3.Error as error:
            raise storage_failure() from error

    def count(self) -> int:
        try:
            with self._db() as connection:
                return connection.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
        except sqlite3.Error as error:
            raise storage_failure() from error
