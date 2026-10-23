from dataclasses import dataclass
from threading import Lock
from typing import ClassVar, Self

from app.users.domain import User, UserRegistration
from app.users.service import UserService
from app.workouts.domain import Workout, WorkoutRegistration, WorkoutUpdate
from app.workouts.service import WorkoutService


@dataclass(frozen=True)
class ApplicationContext:
    users: UserService
    workouts: WorkoutService


class FacadeSingletonController:
    _instance: ClassVar[Self | None] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> Self:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Self:
        return cls()

    def register_user(
        self, context: ApplicationContext, registration: UserRegistration
    ) -> User:
        return context.users.add_user(registration)

    def list_users(self, context: ApplicationContext) -> list[User]:
        return context.users.list_users()

    def create_workout(
        self, context: ApplicationContext, registration: WorkoutRegistration
    ) -> Workout:
        return context.workouts.create_workout(registration)

    def get_workout(self, context: ApplicationContext, workout_id: int) -> Workout:
        return context.workouts.get_workout(workout_id)

    def list_workouts(self, context: ApplicationContext) -> list[Workout]:
        return context.workouts.list_workouts()

    def update_workout(
        self, context: ApplicationContext, workout_id: int, update: WorkoutUpdate
    ) -> Workout:
        return context.workouts.update_workout(workout_id, update)

    def delete_workout(self, context: ApplicationContext, workout_id: int) -> None:
        context.workouts.delete_workout(workout_id)

    def count_entities(self, context: ApplicationContext) -> int:
        return context.users.count_users() + context.workouts.count_workouts()
