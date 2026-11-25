from __future__ import annotations

from dataclasses import dataclass, replace

from app.workouts.policy import (
    MAX_WORKOUT_DESCRIPTION_LENGTH,
    MAX_WORKOUT_NAME_LENGTH,
    MIN_WORKOUT_NAME_LENGTH,
    WORKOUT_DESCRIPTION_ERROR,
    WORKOUT_NAME_ERROR,
)


@dataclass(frozen=True)
class WorkoutRegistration:
    user_id: int
    name: str
    description: str = ""


@dataclass(frozen=True)
class WorkoutUpdate:
    name: str
    description: str = ""


@dataclass(frozen=True)
class WorkoutMemento:
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not MIN_WORKOUT_NAME_LENGTH
            <= len(self.name.strip())
            <= MAX_WORKOUT_NAME_LENGTH
            or len(self.name) > MAX_WORKOUT_NAME_LENGTH
        ):
            raise InvalidWorkoutError(WORKOUT_NAME_ERROR)
        if (
            not isinstance(self.description, str)
            or len(self.description) > MAX_WORKOUT_DESCRIPTION_LENGTH
        ):
            raise InvalidWorkoutError(WORKOUT_DESCRIPTION_ERROR)

    def to_update(self) -> WorkoutUpdate:
        return WorkoutUpdate(self.name, self.description)


@dataclass(frozen=True)
class Workout:
    id: int
    user_id: int
    name: str
    description: str

    def create_memento(self) -> WorkoutMemento:
        return WorkoutMemento(self.name, self.description)

    def restore(self, memento: WorkoutMemento) -> Workout:
        if not isinstance(memento, WorkoutMemento):
            raise TypeError("Memento de treino inválido")
        return replace(self, name=memento.name, description=memento.description)


class InvalidWorkoutError(ValueError):
    pass


class UserNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Usuário não encontrado")


class WorkoutNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Treino não encontrado")
