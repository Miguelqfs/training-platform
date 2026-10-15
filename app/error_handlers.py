from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.users.domain import InvalidCredentialsError, PersistenceError


async def invalid_request(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    # Pydantic inclui a entrada original nos erros, que pode conter a senha.
    details = [
        {key: value for key, value in item.items() if key not in ("input", "ctx")}
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content={"detail": details}
    )


async def invalid_credentials(
    request: Request, error: InvalidCredentialsError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content={"detail": str(error)}
    )


async def persistence_failure(
    request: Request, error: PersistenceError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content={"detail": "Armazenamento de usuários indisponível"},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, invalid_request)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials)
    app.add_exception_handler(PersistenceError, persistence_failure)
