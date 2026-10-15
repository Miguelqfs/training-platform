from pathlib import Path

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.routers.users import router as users_router
from app.users.factory import create_user_repository
from app.users.service import UserService


def create_app(
    *, storage: str | None = None, database_path: Path | None = None
) -> FastAPI:
    app = FastAPI(title="Users API")
    repository = create_user_repository(storage, database_path)
    app.state.user_service = UserService(repository)
    register_error_handlers(app)
    app.include_router(users_router)
    return app


app = create_app()
