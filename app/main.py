from pathlib import Path

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.facade import ApplicationContext
from app.routers.users import router as users_router
from app.users.factory import resolve_storage
from app.users.repository import MemoryUserRepository, SQLiteUserRepository
from app.users.service import UserService
from app.workouts.repository import MemoryWorkoutRepository, SQLiteWorkoutRepository
from app.workouts.service import WorkoutService


def create_app(
    *, storage: str | None = None, database_path: Path | None = None
) -> FastAPI:
    app = FastAPI(title="Training Platform")
    storage, database_path = resolve_storage(storage, database_path)
    repository = (
        MemoryUserRepository()
        if storage == "memory"
        else SQLiteUserRepository(database_path)
    )
    workouts = (
        MemoryWorkoutRepository()
        if storage == "memory"
        else SQLiteWorkoutRepository(database_path)
    )
    app.state.context = ApplicationContext(
        UserService(repository), WorkoutService(workouts, repository)
    )
    register_error_handlers(app)
    app.include_router(users_router)
    return app


app = create_app()
