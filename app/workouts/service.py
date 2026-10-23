from app.users.domain import PersistenceError
from app.users.repository import UserRepository
from app.workouts.domain import (
    InvalidWorkoutError,
    UserNotFoundError,
    Workout,
    WorkoutNotFoundError,
    WorkoutRegistration,
    WorkoutUpdate,
)
from app.workouts.policy import (
    MAX_WORKOUT_DESCRIPTION_LENGTH,
    MAX_WORKOUT_NAME_LENGTH,
    MIN_WORKOUT_NAME_LENGTH,
    WORKOUT_DESCRIPTION_ERROR,
    WORKOUT_NAME_ERROR,
)
from app.workouts.repository import WorkoutRepository


def validate_id(value: int, entity: str) -> None:
    if type(value) is not int or value < 1:
        raise InvalidWorkoutError(f"ID do {entity} deve ser um inteiro positivo")


def normalize_fields(data: WorkoutUpdate) -> WorkoutUpdate:
    if not isinstance(data.name, str):
        raise InvalidWorkoutError(WORKOUT_NAME_ERROR)
    name = data.name.strip()
    if not MIN_WORKOUT_NAME_LENGTH <= len(name) <= MAX_WORKOUT_NAME_LENGTH:
        raise InvalidWorkoutError(WORKOUT_NAME_ERROR)
    if not isinstance(data.description, str):
        raise InvalidWorkoutError(WORKOUT_DESCRIPTION_ERROR)
    description = data.description.strip()
    if len(description) > MAX_WORKOUT_DESCRIPTION_LENGTH:
        raise InvalidWorkoutError(WORKOUT_DESCRIPTION_ERROR)
    return WorkoutUpdate(name, description)


class WorkoutService:
    def __init__(self, repository: WorkoutRepository, users: UserRepository) -> None:
        self._repository = repository
        self._users = users

    def create_workout(self, registration: WorkoutRegistration) -> Workout:
        validate_id(registration.user_id, "usuário")
        fields = normalize_fields(
            WorkoutUpdate(registration.name, registration.description)
        )
        try:
            user = self._users.get_by_id(registration.user_id)
        except PersistenceError as error:
            raise PersistenceError(
                "Não foi possível verificar o usuário do treino",
                public_message=PersistenceError.WORKOUT_MESSAGE,
            ) from error
        if user is None:
            raise UserNotFoundError()
        return self._repository.add(
            WorkoutRegistration(user.id, fields.name, fields.description)
        )

    def get_workout(self, workout_id: int) -> Workout:
        validate_id(workout_id, "treino")
        workout = self._repository.get_by_id(workout_id)
        if workout is None:
            raise WorkoutNotFoundError()
        return workout

    def list_workouts(self) -> list[Workout]:
        return self._repository.list_workouts()

    def update_workout(self, workout_id: int, update: WorkoutUpdate) -> Workout:
        validate_id(workout_id, "treino")
        fields = normalize_fields(update)
        workout = self._repository.update(workout_id, fields)
        if workout is None:
            raise WorkoutNotFoundError()
        return workout

    def delete_workout(self, workout_id: int) -> None:
        validate_id(workout_id, "treino")
        if not self._repository.delete(workout_id):
            raise WorkoutNotFoundError()

    def count_workouts(self) -> int:
        return self._repository.count()
