from collections.abc import Mapping

from app.reports.domain import (
    AccessReportRequest,
    GeneratedReport,
    InvalidReportError,
    ReportFormat,
)
from app.reports.template import AccessReportTemplate


class AccessReportService:
    def __init__(self, templates: Mapping[ReportFormat, AccessReportTemplate]) -> None:
        self._templates = dict(templates)

    def generate(self, request: AccessReportRequest) -> GeneratedReport:
        template = self._templates.get(request.format)
        if template is None:
            raise InvalidReportError("Formato deve ser html ou pdf")
        return template.generate(request.start, request.end)
