import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers.users import router as users_router
from app.users.domain import InvalidCredentialsError, PersistenceError
from app.users.repository import MemoryUserRepository, SQLiteUserRepository
from app.users.service import UserService


def create_app(
    *, storage: str | None = None, database_path: Path | None = None
) -> FastAPI:
    app = FastAPI(title="Users API")
    storage = storage if storage is not None else os.getenv("USER_STORAGE", "memory")
    if storage == "memory":
        repository = MemoryUserRepository()
    elif storage == "sqlite":
        path = (
            database_path
            if database_path is not None
            else Path(os.getenv("USER_DATABASE", "users.sqlite3"))
        )
        repository = SQLiteUserRepository(path)
    else:
        raise ValueError("USER_STORAGE deve ser memory ou sqlite")
    app.state.user_service = UserService(repository)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # Pydantic inclui a entrada original nos erros, que pode conter a senha.
        details = [
            {key: value for key, value in item.items() if key not in ("input", "ctx")}
            for item in error.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials(
        request: Request, error: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(PersistenceError)
    async def persistence_failure(
        request: Request, error: PersistenceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Armazenamento de usuários indisponível"},
        )

    app.include_router(users_router)
    return app


app = create_app()
