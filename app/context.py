from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.reports.service import AccessReportService
from app.users.service import UserService
from app.workouts.service import WorkoutService

if TYPE_CHECKING:
    from app.repositories import Repositories


@dataclass(frozen=True)
class ApplicationContext:
    users: UserService
    workouts: WorkoutService
    reports: AccessReportService
    repositories: "Repositories | None" = None
