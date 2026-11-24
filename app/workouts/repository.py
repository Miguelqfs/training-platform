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
    InvalidWorkoutError,
    UserNotFoundError,
    Workout,
    WorkoutMemento,
    WorkoutNotFoundError,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.ports import WorkoutMementoRepository as WorkoutMementoRepository
from app.workouts.ports import WorkoutRepository as WorkoutRepository


class MemoryWorkoutRepository:
    def __init__(self, lock: RLock | None = None) -> None:
        self._workouts: dict[int, Workout] = {}
        self._next_id = 1
        self._lock = lock if lock is not None else RLock()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            workouts = self._workouts.copy()
            next_id = self._next_id
            try:
                yield
            except BaseException:
                self._workouts = workouts
                self._next_id = next_id
                raise

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


def _is_valid_workout_id(workout_id: int) -> bool:
    return type(workout_id) is int and workout_id >= 1


def _validate_workout_id(workout_id: int) -> None:
    if not _is_valid_workout_id(workout_id):
        raise InvalidWorkoutError("ID do treino deve ser um inteiro positivo")


def _validate_save_input(workout_id: int, memento: WorkoutMemento) -> None:
    _validate_workout_id(workout_id)
    if not isinstance(memento, WorkoutMemento):
        raise TypeError("Memento de treino inválido")


def memento_storage_failure() -> PersistenceError:
    return PersistenceError(
        "Não foi possível acessar o histórico de atualização dos treinos",
        public_message=PersistenceError.WORKOUT_MESSAGE,
    )


class MemoryWorkoutMementoRepository:
    def __init__(self, lock: RLock | None = None) -> None:
        self._mementos: dict[int, WorkoutMemento] = {}
        self._lock = lock if lock is not None else RLock()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            mementos = self._mementos.copy()
            try:
                yield
            except BaseException:
                self._mementos = mementos
                raise

    def save(self, workout_id: int, memento: WorkoutMemento) -> None:
        _validate_save_input(workout_id, memento)
        with self._lock:
            self._mementos[workout_id] = memento

    def get(self, workout_id: int) -> WorkoutMemento | None:
        if not _is_valid_workout_id(workout_id):
            return None
        with self._lock:
            return self._mementos.get(workout_id)

    def consume(self, workout_id: int) -> WorkoutMemento | None:
        if not _is_valid_workout_id(workout_id):
            return None
        with self._lock:
            return self._mementos.pop(workout_id, None)

    def delete(self, workout_id: int) -> bool:
        if not _is_valid_workout_id(workout_id):
            return False
        with self._lock:
            return self._mementos.pop(workout_id, None) is not None


class SQLiteWorkoutMementoRepository:
    def __init__(
        self, path: Path, connection: sqlite3.Connection | None = None
    ) -> None:
        self._path = path
        self._connection = connection
        if connection is not None:
            return
        try:
            with self._db() as connection:
                connection.execute("""CREATE TABLE IF NOT EXISTS workout_mementos (
                    workout_id INTEGER PRIMARY KEY REFERENCES workouts(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                )""")
        except sqlite3.Error as error:
            raise memento_storage_failure() from error

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        if self._connection is not None:
            yield self._connection
        else:
            with sqlite_connection(self._path) as connection:
                yield connection

    def save(self, workout_id: int, memento: WorkoutMemento) -> None:
        _validate_save_input(workout_id, memento)
        try:
            with self._db() as connection:
                connection.execute(
                    """INSERT INTO workout_mementos (workout_id, name, description)
                    VALUES (?, ?, ?)
                    ON CONFLICT(workout_id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description""",
                    (str(workout_id), memento.name, memento.description),
                )
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode in (
                sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY,
                sqlite3.SQLITE_MISMATCH,
            ):
                raise WorkoutNotFoundError() from error
            raise memento_storage_failure() from error
        except sqlite3.Error as error:
            raise memento_storage_failure() from error

    def get(self, workout_id: int) -> WorkoutMemento | None:
        if not _is_valid_workout_id(workout_id):
            return None
        try:
            with self._db() as connection:
                row = connection.execute(
                    "SELECT name, description FROM workout_mementos WHERE workout_id = ?",
                    (str(workout_id),),
                ).fetchone()
            return WorkoutMemento(*row) if row is not None else None
        except sqlite3.Error as error:
            raise memento_storage_failure() from error

    def consume(self, workout_id: int) -> WorkoutMemento | None:
        if not _is_valid_workout_id(workout_id):
            return None
        try:
            with self._db() as connection:
                # Drains RETURNING rows so SQLite finishes the statement before commit/rollback.
                rows = connection.execute(
                    "DELETE FROM workout_mementos WHERE workout_id = ? RETURNING name, description",
                    (str(workout_id),),
                ).fetchall()
            return WorkoutMemento(*rows[0]) if rows else None
        except sqlite3.Error as error:
            raise memento_storage_failure() from error

    def delete(self, workout_id: int) -> bool:
        if not _is_valid_workout_id(workout_id):
            return False
        try:
            with self._db() as connection:
                return (
                    connection.execute(
                        "DELETE FROM workout_mementos WHERE workout_id = ?",
                        (str(workout_id),),
                    ).rowcount
                    > 0
                )
        except sqlite3.Error as error:
            raise memento_storage_failure() from error
