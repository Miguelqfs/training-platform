from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI

from app.accesses.logging_adapter import LoggingAccessLogAdapter
from app.accesses.ports import AccessLogPort
from app.error_handlers import register_error_handlers
from app.facade import ApplicationContext
from app.reports.renderers import HtmlAccessReport, PdfAccessReport
from app.reports.service import AccessReportService
from app.repositories import repository_factory
from app.routers.statistics import router as statistics_router
from app.routers.users import router as users_router
from app.routers.workouts import router as workouts_router
from app.users.factory import resolve_storage
from app.users.service import UserService
from app.workouts.service import WorkoutService, utc_now


def create_app(
    *,
    storage: str | None = None,
    database_path: Path | None = None,
    access_log: AccessLogPort | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> FastAPI:
    app = FastAPI(title="Training Platform")
    storage, database_path = resolve_storage(storage, database_path)
    repositories = repository_factory(storage, database_path).create()
    app.state.context = ApplicationContext(
        UserService(repositories.users),
        WorkoutService(
            repositories.workouts,
            repositories.users,
            repositories.unit_of_work,
            access_log=access_log
            if access_log is not None
            else LoggingAccessLogAdapter(),
            clock=clock,
        ),
        AccessReportService(
            {
                "html": HtmlAccessReport(repositories.accesses),
                "pdf": PdfAccessReport(repositories.accesses),
            }
        ),
        repositories=repositories,
    )
    register_error_handlers(app)
    app.include_router(users_router)
    app.include_router(workouts_router)
    app.include_router(statistics_router)
    return app


app = create_app()
