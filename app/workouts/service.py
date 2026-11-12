from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from app.accesses.domain import AccessEvent, Operation
from app.accesses.ports import AccessLogPort
from app.unit_of_work import TransactionRepositories, UnitOfWork
from app.users.domain import PersistenceError
from app.users.ports import UserRepository
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
from app.workouts.ports import WorkoutRepository


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


def utc_now() -> datetime:
    return datetime.now(UTC)


class WorkoutService:
    def __init__(
        self,
        repository: WorkoutRepository,
        users: UserRepository,
        unit_of_work: UnitOfWork,
        *,
        access_log: AccessLogPort,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._users = users
        self._unit_of_work = unit_of_work
        self._access_log = access_log
        self._clock = clock

    @contextmanager
    def _transaction(self) -> Iterator[TransactionRepositories]:
        try:
            with self._unit_of_work.transaction() as tx:
                yield tx
        except PersistenceError as error:
            raise PersistenceError(
                "Não foi possível concluir a operação de treino e seu evento",
                public_message=PersistenceError.WORKOUT_MESSAGE,
            ) from error

    def _record(
        self, tx: TransactionRepositories, workout: Workout, operation: Operation
    ) -> AccessEvent:
        event = AccessEvent(workout.user_id, operation, self._clock())
        tx.accesses.add(event)
        return event

    def _log(self, event: AccessEvent) -> None:
        try:
            self._access_log.record(event)
        except Exception:
            # O log auxiliar não pode desfazer o commit nem tentar logar a própria falha.
            pass

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
        with self._transaction() as tx:
            workout = tx.workouts.add(
                WorkoutRegistration(user.id, fields.name, fields.description)
            )
            event = self._record(tx, workout, "create")
        self._log(event)
        return workout

    def get_workout(self, workout_id: int) -> Workout:
        validate_id(workout_id, "treino")
        with self._transaction() as tx:
            workout = tx.workouts.get_by_id(workout_id)
            if workout is None:
                raise WorkoutNotFoundError()
            event = self._record(tx, workout, "get")
        self._log(event)
        return workout

    def list_workouts(self) -> list[Workout]:
        return self._repository.list_workouts()

    def update_workout(self, workout_id: int, update: WorkoutUpdate) -> Workout:
        validate_id(workout_id, "treino")
        fields = normalize_fields(update)
        with self._transaction() as tx:
            workout = tx.workouts.update(workout_id, fields)
            if workout is None:
                raise WorkoutNotFoundError()
            event = self._record(tx, workout, "update")
        self._log(event)
        return workout

    def delete_workout(self, workout_id: int) -> None:
        validate_id(workout_id, "treino")
        with self._transaction() as tx:
            workout = tx.workouts.get_by_id(workout_id)
            if workout is None or not tx.workouts.delete(workout_id):
                raise WorkoutNotFoundError()
            event = self._record(tx, workout, "delete")
        self._log(event)

    def count_workouts(self) -> int:
        return self._repository.count()
