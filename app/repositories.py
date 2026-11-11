"""Composition of repositories and coordinated workout/event writes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Protocol

from app.accesses.repository import (
    AccessEventRepository,
    MemoryAccessEventRepository,
    SQLiteAccessEventRepository,
)
from app.storage import sqlite_connection
from app.users.domain import PersistenceError
from app.users.repository import (
    MemoryUserRepository,
    SQLiteUserRepository,
    UserRepository,
)
from app.workouts.repository import (
    MemoryWorkoutRepository,
    SQLiteWorkoutRepository,
    WorkoutRepository,
)


@dataclass(frozen=True)
class TransactionRepositories:
    workouts: WorkoutRepository
    accesses: AccessEventRepository


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractContextManager[TransactionRepositories]: ...


class MemoryUnitOfWork:
    def __init__(
        self,
        workouts: MemoryWorkoutRepository,
        accesses: MemoryAccessEventRepository,
        lock: RLock,
    ) -> None:
        self._workouts, self._accesses, self._lock = workouts, accesses, lock

    @contextmanager
    def transaction(self) -> Iterator[TransactionRepositories]:
        with self._lock:
            workouts = self._workouts._workouts.copy()
            next_id = self._workouts._next_id
            events = self._accesses._events.copy()
            try:
                yield TransactionRepositories(self._workouts, self._accesses)
            except BaseException:
                self._workouts._workouts = workouts
                self._workouts._next_id = next_id
                self._accesses._events = events
                raise


class SQLiteUnitOfWork:
    def __init__(self, path: Path) -> None:
        self._path = path

    @contextmanager
    def transaction(self) -> Iterator[TransactionRepositories]:
        try:
            with sqlite_connection(self._path) as connection:
                # Begin before reads so a transaction sees a consistent workout.
                connection.execute("BEGIN")
                yield TransactionRepositories(
                    SQLiteWorkoutRepository(self._path, connection),
                    SQLiteAccessEventRepository(self._path, connection),
                )
        except sqlite3.Error as error:
            raise PersistenceError("Não foi possível concluir a transação") from error


@dataclass(frozen=True)
class Repositories:
    users: UserRepository
    workouts: WorkoutRepository
    accesses: AccessEventRepository
    unit_of_work: UnitOfWork


class RepositoryFactory(Protocol):
    def create(self) -> Repositories: ...


class MemoryRepositoryFactory:
    def create(self) -> Repositories:
        lock = RLock()
        workouts = MemoryWorkoutRepository(lock)
        accesses = MemoryAccessEventRepository(lock)
        return Repositories(
            MemoryUserRepository(),
            workouts,
            accesses,
            MemoryUnitOfWork(workouts, accesses, lock),
        )


class SQLiteRepositoryFactory:
    def __init__(self, path: Path) -> None:
        self._path = path

    def create(self) -> Repositories:
        users = SQLiteUserRepository(self._path)
        workouts = SQLiteWorkoutRepository(self._path)
        accesses = SQLiteAccessEventRepository(self._path)
        return Repositories(users, workouts, accesses, SQLiteUnitOfWork(self._path))


def repository_factory(storage: str, path: Path) -> RepositoryFactory:
    if storage == "memory":
        return MemoryRepositoryFactory()
    if storage == "sqlite":
        return SQLiteRepositoryFactory(path)
    raise ValueError("Armazenamento deve ser memory ou sqlite")
