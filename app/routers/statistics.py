from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import Context
from app.facade import FacadeSingletonController
from app.reports.domain import AccessReportRequest, ReportFormat, ReportGenerationError
from app.reports.schemas import RFC3339Instant
from app.schemas import ErrorMessage, ValidationErrorResponse
from app.workouts.schemas import EntityCount

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorMessage,
            "description": "Armazenamento de usuários ou treinos indisponível",
        }
    },
)


@router.get("/entities", response_model=EntityCount)
def count_entities(context: Context) -> EntityCount:
    return EntityCount(
        total=FacadeSingletonController.get_instance().count_entities(context)
    )


@router.get(
    "/accesses",
    response_class=Response,
    responses={
        200: {
            "description": "Relatório de acessos por proprietário de treino",
            "content": {
                "text/html": {"schema": {"type": "string"}},
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
            },
        },
        422: {"model": ValidationErrorResponse, "description": "Parâmetros inválidos"},
        503: {
            "model": ErrorMessage,
            "description": ReportGenerationError.PUBLIC_MESSAGE,
        },
    },
)
def access_report(
    context: Context,
    start: Annotated[
        RFC3339Instant, Query(description="Início inclusivo em RFC 3339 com fuso")
    ],
    end: Annotated[
        RFC3339Instant, Query(description="Fim exclusivo em RFC 3339 com fuso")
    ],
    format: Annotated[ReportFormat, Query(description="Formato do relatório")],
) -> Response:
    report = FacadeSingletonController.get_instance().generate_access_report(
        context, AccessReportRequest(start, end, format)
    )
    return Response(content=report.content, media_type=report.media_type)
