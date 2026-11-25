"""Comandos das operações de negócio expostas pela fachada.

Cada comando é imutável, guarda apenas os argumentos da operação e recebe o
contexto da aplicação somente em ``execute``. Assim um mesmo comando não fica
preso a uma aplicação e a fachada continua sem estado de negócio.
"""

from dataclasses import dataclass
from typing import Protocol, TypeVar

from app.context import ApplicationContext
from app.reports.domain import AccessReportRequest, GeneratedReport
from app.users.domain import User, UserRegistration
from app.workouts.domain import Workout, WorkoutRegistration, WorkoutUpdate

Result = TypeVar("Result", covariant=True)


class Command(Protocol[Result]):
    def execute(self, context: ApplicationContext) -> Result: ...


@dataclass(frozen=True)
class RegisterUserCommand:
    registration: UserRegistration

    def execute(self, context: ApplicationContext) -> User:
        return context.users.add_user(self.registration)


@dataclass(frozen=True)
class ListUsersCommand:
    def execute(self, context: ApplicationContext) -> list[User]:
        return context.users.list_users()


@dataclass(frozen=True)
class CreateWorkoutCommand:
    registration: WorkoutRegistration

    def execute(self, context: ApplicationContext) -> Workout:
        return context.workouts.create_workout(self.registration)


@dataclass(frozen=True)
class GetWorkoutCommand:
    workout_id: int

    def execute(self, context: ApplicationContext) -> Workout:
        return context.workouts.get_workout(self.workout_id)


@dataclass(frozen=True)
class ListWorkoutsCommand:
    def execute(self, context: ApplicationContext) -> list[Workout]:
        return context.workouts.list_workouts()


@dataclass(frozen=True)
class UpdateWorkoutCommand:
    workout_id: int
    update: WorkoutUpdate

    def execute(self, context: ApplicationContext) -> Workout:
        return context.workouts.update_workout(self.workout_id, self.update)


@dataclass(frozen=True)
class UndoWorkoutCommand:
    workout_id: int

    def execute(self, context: ApplicationContext) -> Workout:
        return context.workouts.undo_workout(self.workout_id)


@dataclass(frozen=True)
class DeleteWorkoutCommand:
    workout_id: int

    def execute(self, context: ApplicationContext) -> None:
        context.workouts.delete_workout(self.workout_id)


@dataclass(frozen=True)
class CountEntitiesCommand:
    def execute(self, context: ApplicationContext) -> int:
        return context.users.count_users() + context.workouts.count_workouts()


@dataclass(frozen=True)
class GenerateAccessReportCommand:
    request: AccessReportRequest

    def execute(self, context: ApplicationContext) -> GeneratedReport:
        return context.reports.generate(self.request)
