from dataclasses import dataclass


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
class Workout:
    id: int
    user_id: int
    name: str
    description: str


class InvalidWorkoutError(ValueError):
    pass


class UserNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Usuário não encontrado")


class WorkoutNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Treino não encontrado")
