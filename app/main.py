from pathlib import Path

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.facade import ApplicationContext
from app.repositories import repository_factory
from app.routers.statistics import router as statistics_router
from app.routers.users import router as users_router
from app.routers.workouts import router as workouts_router
from app.users.factory import resolve_storage
from app.users.service import UserService
from app.workouts.service import WorkoutService


def create_app(
    *, storage: str | None = None, database_path: Path | None = None
) -> FastAPI:
    app = FastAPI(title="Training Platform")
    storage, database_path = resolve_storage(storage, database_path)
    repositories = repository_factory(storage, database_path).create()
    app.state.context = ApplicationContext(
        UserService(repositories.users),
        WorkoutService(repositories.workouts, repositories.users),
        repositories=repositories,
    )
    register_error_handlers(app)
    app.include_router(users_router)
    app.include_router(workouts_router)
    app.include_router(statistics_router)
    return app


app = create_app()
