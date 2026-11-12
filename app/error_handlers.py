from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.reports.domain import InvalidReportError, ReportGenerationError
from app.users.domain import InvalidCredentialsError, PersistenceError
from app.workouts.domain import (
    InvalidWorkoutError,
    UserNotFoundError,
    WorkoutNotFoundError,
)


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


async def invalid_domain_fields(
    request: Request,
    error: InvalidCredentialsError | InvalidWorkoutError | InvalidReportError,
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content={"detail": str(error)}
    )


async def persistence_failure(
    request: Request, error: PersistenceError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content={"detail": error.public_message},
    )


async def entity_not_found(
    request: Request, error: UserNotFoundError | WorkoutNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND, content={"detail": str(error)}
    )


async def report_failure(
    request: Request, error: ReportGenerationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content={"detail": ReportGenerationError.PUBLIC_MESSAGE},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, invalid_request)
    app.add_exception_handler(InvalidCredentialsError, invalid_domain_fields)
    app.add_exception_handler(PersistenceError, persistence_failure)
    app.add_exception_handler(InvalidWorkoutError, invalid_domain_fields)
    app.add_exception_handler(UserNotFoundError, entity_not_found)
    app.add_exception_handler(WorkoutNotFoundError, entity_not_found)
    app.add_exception_handler(InvalidReportError, invalid_domain_fields)
    app.add_exception_handler(ReportGenerationError, report_failure)
