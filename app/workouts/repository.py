from dataclasses import replace
from threading import Lock
from typing import Protocol

from app.workouts.domain import (
    Workout,
    WorkoutRegistration,
    WorkoutUpdate,
)


class WorkoutRepository(Protocol):
    def add(self, data: WorkoutRegistration) -> Workout: ...
    def get_by_id(self, workout_id: int) -> Workout | None: ...
    def list_workouts(self) -> list[Workout]: ...
    def update(self, workout_id: int, data: WorkoutUpdate) -> Workout | None: ...
    def delete(self, workout_id: int) -> bool: ...
    def count(self) -> int: ...


class MemoryWorkoutRepository:
    def __init__(self) -> None:
        self._workouts: dict[int, Workout] = {}
        self._next_id = 1
        self._lock = Lock()

    def add(self, data: WorkoutRegistration) -> Workout:
        with self._lock:
            workout = Workout(self._next_id, data.user_id, data.name, data.description)
            self._workouts[workout.id] = workout
            self._next_id += 1
            return workout

    def get_by_id(self, workout_id: int) -> Workout | None:
        with self._lock:
            return self._workouts.get(workout_id)

    def list_workouts(self) -> list[Workout]:
        with self._lock:
            return sorted(self._workouts.values(), key=lambda workout: workout.id)

    def update(self, workout_id: int, data: WorkoutUpdate) -> Workout | None:
        with self._lock:
            workout = self._workouts.get(workout_id)
            if workout is None:
                return None
            updated = replace(workout, name=data.name, description=data.description)
            self._workouts[workout_id] = updated
            return updated

    def delete(self, workout_id: int) -> bool:
        with self._lock:
            return self._workouts.pop(workout_id, None) is not None

    def count(self) -> int:
        with self._lock:
            return len(self._workouts)
