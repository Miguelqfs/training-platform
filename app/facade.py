from threading import Lock
from typing import ClassVar, Self, TypeVar

from app.commands import (
    Command,
    CountEntitiesCommand,
    CreateWorkoutCommand,
    DeleteWorkoutCommand,
    GenerateAccessReportCommand,
    GetWorkoutCommand,
    ListUsersCommand,
    ListWorkoutsCommand,
    RegisterUserCommand,
    UpdateWorkoutCommand,
)
from app.context import ApplicationContext
from app.reports.domain import AccessReportRequest, GeneratedReport
from app.users.domain import User, UserRegistration
from app.workouts.domain import Workout, WorkoutRegistration, WorkoutUpdate

__all__ = ["ApplicationContext", "FacadeSingletonController"]

Result = TypeVar("Result")


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

    def execute(self, context: ApplicationContext, command: Command[Result]) -> Result:
        return command.execute(context)

    def register_user(
        self, context: ApplicationContext, registration: UserRegistration
    ) -> User:
        return self.execute(context, RegisterUserCommand(registration))

    def list_users(self, context: ApplicationContext) -> list[User]:
        return self.execute(context, ListUsersCommand())

    def create_workout(
        self, context: ApplicationContext, registration: WorkoutRegistration
    ) -> Workout:
        return self.execute(context, CreateWorkoutCommand(registration))

    def get_workout(self, context: ApplicationContext, workout_id: int) -> Workout:
        return self.execute(context, GetWorkoutCommand(workout_id))

    def list_workouts(self, context: ApplicationContext) -> list[Workout]:
        return self.execute(context, ListWorkoutsCommand())

    def update_workout(
        self, context: ApplicationContext, workout_id: int, update: WorkoutUpdate
    ) -> Workout:
        return self.execute(context, UpdateWorkoutCommand(workout_id, update))

    def delete_workout(self, context: ApplicationContext, workout_id: int) -> None:
        self.execute(context, DeleteWorkoutCommand(workout_id))

    def count_entities(self, context: ApplicationContext) -> int:
        return self.execute(context, CountEntitiesCommand())

    def generate_access_report(
        self, context: ApplicationContext, request: AccessReportRequest
    ) -> GeneratedReport:
        return self.execute(context, GenerateAccessReportCommand(request))
