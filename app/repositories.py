"""Composition of repositories and coordinated workout, event, and memento writes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
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
from app.unit_of_work import TransactionRepositories, UnitOfWork
from app.users.domain import PersistenceError
from app.users.repository import (
    MemoryUserRepository,
    SQLiteUserRepository,
    UserRepository,
)
from app.workouts.repository import (
    MemoryWorkoutMementoRepository,
    MemoryWorkoutRepository,
    SQLiteWorkoutMementoRepository,
    SQLiteWorkoutRepository,
    WorkoutMementoRepository,
    WorkoutRepository,
)


class MemoryUnitOfWork:
    def __init__(
        self,
        workouts: MemoryWorkoutRepository,
        accesses: MemoryAccessEventRepository,
        mementos: MemoryWorkoutMementoRepository,
        lock: RLock,
    ) -> None:
        self._workouts = workouts
        self._accesses = accesses
        self._mementos = mementos
        self._lock = lock

    @contextmanager
    def transaction(self) -> Iterator[TransactionRepositories]:
        with (
            self._lock,
            self._workouts.transaction(),
            self._accesses.transaction(),
            self._mementos.transaction(),
        ):
            yield TransactionRepositories(
                self._workouts, self._accesses, self._mementos
            )


class SQLiteUnitOfWork:
    def __init__(self, path: Path) -> None:
        self._path = path

    @contextmanager
    def transaction(self) -> Iterator[TransactionRepositories]:
        try:
            with sqlite_connection(self._path) as connection:
                # Acquire write lock upfront so read-modify-write transactions serialize.
                connection.execute("BEGIN IMMEDIATE")
                yield TransactionRepositories(
                    SQLiteWorkoutRepository(self._path, connection),
                    SQLiteAccessEventRepository(self._path, connection),
                    SQLiteWorkoutMementoRepository(self._path, connection),
                )
        except sqlite3.Error as error:
            raise PersistenceError(
                "Não foi possível concluir a transação",
                public_message=PersistenceError.WORKOUT_MESSAGE,
            ) from error


@dataclass(frozen=True)
class Repositories:
    users: UserRepository
    workouts: WorkoutRepository
    accesses: AccessEventRepository
    mementos: WorkoutMementoRepository
    unit_of_work: UnitOfWork


class RepositoryFactory(Protocol):
    def create(self) -> Repositories: ...


class MemoryRepositoryFactory:
    def create(self) -> Repositories:
        lock = RLock()
        workouts = MemoryWorkoutRepository(lock)
        accesses = MemoryAccessEventRepository(lock)
        mementos = MemoryWorkoutMementoRepository(lock)
        return Repositories(
            MemoryUserRepository(),
            workouts,
            accesses,
            mementos,
            MemoryUnitOfWork(workouts, accesses, mementos, lock),
        )


class SQLiteRepositoryFactory:
    def __init__(self, path: Path) -> None:
        self._path = path

    def create(self) -> Repositories:
        users = SQLiteUserRepository(self._path)
        workouts = SQLiteWorkoutRepository(self._path)
        accesses = SQLiteAccessEventRepository(self._path)
        mementos = SQLiteWorkoutMementoRepository(self._path)
        return Repositories(
            users, workouts, accesses, mementos, SQLiteUnitOfWork(self._path)
        )


def repository_factory(storage: str, path: Path) -> RepositoryFactory:
    if storage == "memory":
        return MemoryRepositoryFactory()
    if storage == "sqlite":
        return SQLiteRepositoryFactory(path)
    raise ValueError("Armazenamento deve ser memory ou sqlite")
