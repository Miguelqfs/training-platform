from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar, final

from app.accesses.domain import interval
from app.accesses.ports import AccessEventRepository
from app.reports.domain import (
    AccessReport,
    GeneratedReport,
    InvalidReportError,
    ReportGenerationError,
    aggregate,
)


class AccessReportTemplate(ABC):
    media_type: ClassVar[str]

    def __init__(self, repository: AccessEventRepository) -> None:
        self._repository = repository

    @final
    def generate(self, start: datetime, end: datetime) -> GeneratedReport:
        try:
            start, end = interval(start, end)
        except ValueError as error:
            raise InvalidReportError(str(error)) from error
        try:
            events = self._repository.list_between(start, end)
            report = aggregate(start, end, events)
            return GeneratedReport(self.render(report), self.media_type)
        except Exception as error:
            raise ReportGenerationError(ReportGenerationError.PUBLIC_MESSAGE) from error

    @abstractmethod
    def render(self, report: AccessReport) -> bytes: ...
