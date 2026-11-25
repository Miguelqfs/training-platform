"""Business-facing transaction contract for coordinated workout, event, and memento writes."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from app.accesses.ports import AccessEventRepository
from app.workouts.ports import WorkoutMementoRepository, WorkoutRepository


@dataclass(frozen=True)
class TransactionRepositories:
    workouts: WorkoutRepository
    accesses: AccessEventRepository
    mementos: WorkoutMementoRepository


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractContextManager[TransactionRepositories]: ...
