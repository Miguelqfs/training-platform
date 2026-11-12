import re
import sqlite3
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from html.parser import HTMLParser
from io import BytesIO
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.accesses.domain import AccessEvent
from app.facade import FacadeSingletonController
from app.main import create_app
from app.reports.domain import (
    AccessReportRequest,
    GeneratedReport,
    InvalidReportError,
    ReportGenerationError,
)
from app.reports.renderers import HtmlAccessReport, PdfAccessReport
from app.reports.service import AccessReportService
from app.reports.template import AccessReportTemplate
from app.users.domain import NewUser, PersistenceError, UserRole

START = datetime(2026, 11, 11, tzinfo=UTC)
END = START + timedelta(days=1)
PARAMS = {"start": START.isoformat(), "end": END.isoformat(), "format": "html"}
EVENTS = [
    AccessEvent(1, "delete", START - timedelta(microseconds=1)),
    AccessEvent(2, "get", START),
    AccessEvent(1, "create", START + timedelta(hours=1)),
    AccessEvent(2, "get", START + timedelta(hours=2)),
    AccessEvent(1, "update", END - timedelta(microseconds=1)),
    AccessEvent(1, "delete", END),
]


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def report_text(response):
    if response.headers["content-type"] == "application/pdf":
        return " ".join(
            page.extract_text() for page in PdfReader(BytesIO(response.content)).pages
        )
    parser = TextParser()
    parser.feed(response.text)
    return " ".join(parser.parts)


def facts(response):
    text = " ".join(report_text(response).split())
    users = text.split("Por proprietário")[1].split("Por operação")[0]
    operations = text.split("Por operação")[1]
    return {
        "start": re.search(r"Início \(UTC\): (\S+)", text)[1],
        "end": re.search(r"Fim \(UTC\): (\S+)", text)[1],
        "total": int(re.search(r"Total de acessos: (\d+)", text)[1]),
        "users": tuple(
            (int(user), int(count))
            for user, count in re.findall(r"\b(\d+) (\d+)\b", users)
        ),
        "operations": tuple(
            (operation, int(count))
            for operation, count in re.findall(
                r"\b(create|get|update|delete) (\d+)\b", operations
            )
        ),
    }


@pytest.fixture(params=["memory", "sqlite"])
def client(request, tmp_path):
    app = create_app(
        storage=request.param,
        database_path=tmp_path / "reports.db",
        clock=lambda: START,
    )
    repos = app.state.context.repositories
    for username in ("primeiro", "segundo"):
        repos.users.add(
            NewUser(
                username, f"{username}@example.com", UserRole.STUDENT, "private-hash"
            )
        )
    with TestClient(app) as client:
        yield client


@pytest.fixture
def populated(client):
    for event in EVENTS:
        client.app.state.context.repositories.accesses.add(event)
    return client


def test_formats_have_equivalent_filtered_sorted_counts_without_new_events(populated):
    repos = populated.app.state.context.repositories
    before = repos.accesses.list_between(
        START - timedelta(days=1), END + timedelta(days=1)
    )
    responses = [
        populated.get("/statistics/accesses", params={**PARAMS, "format": format})
        for format in ("html", "pdf")
    ]
    assert [response.status_code for response in responses] == [200, 200]
    assert [response.headers["content-type"] for response in responses] == [
        "text/html; charset=utf-8",
        "application/pdf",
    ]
    expected = {
        "start": START.isoformat(),
        "end": END.isoformat(),
        "total": 4,
        "users": ((1, 2), (2, 2)),
        "operations": (("create", 1), ("get", 2), ("update", 1), ("delete", 0)),
    }
    assert facts(responses[0]) == facts(responses[1]) == expected
    assert (
        sum(count for _, count in expected["users"])
        == sum(count for _, count in expected["operations"])
        == expected["total"]
    )
    assert (
        repos.accesses.list_between(START - timedelta(days=1), END + timedelta(days=1))
        == before
    )
    assert populated.get("/statistics/entities").json() == {"total": 2}


@pytest.mark.parametrize("format", ["html", "pdf"])
def test_empty_period_has_zero_counts_and_no_users(populated, format):
    response = populated.get(
        "/statistics/accesses",
        params={
            "start": END.isoformat(),
            "end": (END + timedelta(seconds=1)).isoformat(),
            "format": format,
        },
    )
    assert response.status_code == 200
    # Um evento no início do intervalo deve ser incluído, mesmo quando só há um.
    assert facts(response)["total"] == 1
    response = populated.get(
        "/statistics/accesses",
        params={
            "start": (END + timedelta(seconds=1)).isoformat(),
            "end": (END + timedelta(seconds=2)).isoformat(),
            "format": format,
        },
    )
    result = facts(response)
    assert result["total"] == 0
    assert result["users"] == ()
    assert result["operations"] == (
        ("create", 0),
        ("get", 0),
        ("update", 0),
        ("delete", 0),
    )
    assert "Nenhum acesso no período." in report_text(response)


@pytest.mark.parametrize("format", ["html", "pdf"])
def test_explicit_offsets_are_normalized_to_utc(populated, format):
    local = timezone(timedelta(hours=-3))
    response = populated.get(
        "/statistics/accesses",
        params={
            "start": START.astimezone(local).isoformat(),
            "end": END.astimezone(local).isoformat(),
            "format": format,
        },
    )
    assert response.status_code == 200
    assert facts(response)["start"] == START.isoformat()
    assert facts(response)["end"] == END.isoformat()
    assert facts(response)["total"] == 4


@pytest.mark.parametrize(
    "patch,missing",
    [
        ({}, "start"),
        ({}, "end"),
        ({}, "format"),
        ({"start": "2026-11-11T00:00:00"}, None),
        ({"end": "2026-11-12"}, None),
        ({"start": "1794355200"}, None),
        ({"start": "2026-11-11 00:00:00Z"}, None),
        ({"start": "2026-11-11T00:00Z"}, None),
        ({"start": "2026-02-30T00:00:00Z"}, None),
        ({"start": "2026-11-11T00:00:00+25:00"}, None),
        ({"start": "private-secret"}, None),
        ({"format": "private-secret"}, None),
        ({"format": "PDF"}, None),
        ({"format": ""}, None),
        ({"start": END.isoformat()}, None),
        ({"start": (END + timedelta(seconds=1)).isoformat()}, None),
    ],
)
def test_invalid_queries_are_422_without_reading_or_exposing_inputs(
    client, monkeypatch, patch, missing
):
    repository = client.app.state.context.repositories.accesses
    read = Mock(side_effect=AssertionError("Não deve consultar armazenamento"))
    monkeypatch.setattr(repository, "list_between", read)
    params = {**PARAMS, **patch}
    if missing:
        params.pop(missing)
    response = client.get("/statistics/accesses", params=params)
    assert response.status_code == 422
    assert "private-secret" not in response.text
    assert '"input"' not in response.text and '"ctx"' not in response.text
    read.assert_not_called()


@pytest.mark.parametrize("format", ["html", "pdf"])
@pytest.mark.parametrize("stage", ["repository", "renderer"])
def test_read_and_render_failures_are_generic_503_and_preserve_events(
    populated, monkeypatch, format, stage
):
    repos = populated.app.state.context.repositories
    before = repos.accesses.list_between(START, END)
    error = (
        PersistenceError("private SQL /path password")
        if stage == "repository"
        else RuntimeError("private PDF /path password")
    )
    target = (
        repos.accesses
        if stage == "repository"
        else (HtmlAccessReport if format == "html" else PdfAccessReport)
    )
    method = "list_between" if stage == "repository" else "render"
    with monkeypatch.context() as patch:
        patch.setattr(target, method, Mock(side_effect=error))
        response = populated.get(
            "/statistics/accesses", params={**PARAMS, "format": format}
        )
    assert response.status_code == 503
    assert response.json() == {"detail": ReportGenerationError.PUBLIC_MESSAGE}
    assert repos.accesses.list_between(START, END) == before


@pytest.mark.parametrize("client", ["sqlite"], indirect=True)
@pytest.mark.parametrize("format", ["html", "pdf"])
def test_actual_missing_event_table_returns_503(client, tmp_path, format):
    with sqlite3.connect(tmp_path / "reports.db") as db:
        db.execute("DROP TABLE access_events")
    response = client.get("/statistics/accesses", params={**PARAMS, "format": format})
    assert response.status_code == 503
    assert response.json() == {"detail": ReportGenerationError.PUBLIC_MESSAGE}


def test_template_validates_reads_once_aggregates_then_renders():
    steps = []

    class Repository:
        def list_between(self, start, end):
            steps.append(("read", start, end))
            return EVENTS[1:5]

    class InspectReport(AccessReportTemplate):
        media_type = "text/plain"

        def render(self, report):
            steps.append(("render", report))
            with pytest.raises(FrozenInstanceError):
                report.total = 999
            return b"report"

    template = InspectReport(Repository())
    local = timezone(timedelta(hours=3))
    result = template.generate(START.astimezone(local), END.astimezone(local))
    assert result == GeneratedReport(b"report", "text/plain")
    assert steps[0] == ("read", START, END)
    assert len(steps) == 2
    report = steps[1][1]
    assert (report.start, report.end, report.total) == (START, END, 4)
    assert report.users == ((1, 2), (2, 2))
    assert report.operations == (
        ("create", 1),
        ("get", 2),
        ("update", 1),
        ("delete", 0),
    )


@pytest.mark.parametrize("renderer", [HtmlAccessReport, PdfAccessReport])
@pytest.mark.parametrize(
    "start,end", [(START, START), (END, START), (START.replace(tzinfo=None), END)]
)
def test_direct_business_call_rejects_invalid_period_before_read(renderer, start, end):
    repository = Mock()
    with pytest.raises(InvalidReportError):
        renderer(repository).generate(start, end)
    repository.list_between.assert_not_called()


def test_business_service_rejects_unknown_format_and_preserves_failure_cause():
    repository = Mock()
    error = PersistenceError("private SQL /path")
    repository.list_between.side_effect = error
    service = AccessReportService({"html": HtmlAccessReport(repository)})
    with pytest.raises(InvalidReportError):
        service.generate(AccessReportRequest(START, END, "invalid"))
    repository.list_between.assert_not_called()
    with pytest.raises(ReportGenerationError) as caught:
        service.generate(AccessReportRequest(START, END, "html"))
    assert caught.value.__cause__ is error


@pytest.mark.parametrize("format", ["html", "pdf"])
def test_route_and_facade_delegate_with_application_context(
    client, monkeypatch, format
):
    calls = []
    expected = GeneratedReport(b"substituto", "text/plain")

    def substitute(self, context, request):
        calls.append((self, context, request))
        return expected

    monkeypatch.setattr(FacadeSingletonController, "generate_access_report", substitute)
    response = client.get("/statistics/accesses", params={**PARAMS, "format": format})
    assert response.status_code == 200 and response.content == expected.content
    assert calls == [
        (
            FacadeSingletonController.get_instance(),
            client.app.state.context,
            AccessReportRequest(START, END, format),
        )
    ]


def test_openapi_documents_formats_parameters_and_errors(client):
    operation = client.get("/openapi.json").json()["paths"]["/statistics/accesses"][
        "get"
    ]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert all(parameters[name]["required"] for name in ("start", "end", "format"))
    assert parameters["format"]["schema"]["enum"] == ["html", "pdf"]
    assert parameters["start"]["schema"]["format"] == "date-time"
    assert set(operation["responses"]["200"]["content"]) == {
        "text/html",
        "application/pdf",
    }
    for status, schema in (("422", "ValidationErrorResponse"), ("503", "ErrorMessage")):
        assert operation["responses"][status]["content"]["application/json"]["schema"][
            "$ref"
        ].endswith("/" + schema)


def test_real_workout_events_feed_both_reports_without_sensitive_fields(client):
    body = {
        "user_id": 2,
        "name": "SenhaPrivada12",
        "description": "private@example.com",
    }
    assert client.post("/workouts/", json=body).status_code == 201
    assert client.get("/workouts/1").status_code == 200
    assert client.put("/workouts/1", json={"name": "Novo"}).status_code == 200
    assert client.delete("/workouts/1").status_code == 204
    for format in ("html", "pdf"):
        response = client.get(
            "/statistics/accesses", params={**PARAMS, "format": format}
        )
        assert response.status_code == 200
        result = facts(response)
        assert result["users"] == ((2, 4),)
        assert result["operations"] == (
            ("create", 1),
            ("get", 1),
            ("update", 1),
            ("delete", 1),
        )
        assert all(
            secret not in report_text(response)
            for secret in (
                "SenhaPrivada12",
                "private@example.com",
                "private-hash",
                "password",
            )
        )
    assert client.get("/statistics/entities").json() == {"total": 2}


def test_pdf_paginates_and_repeats_table_headers_without_losing_rows():
    repository = Mock()
    repository.list_between.return_value = [
        AccessEvent(user_id, "get", START) for user_id in range(1, 151)
    ]
    report = PdfAccessReport(repository).generate(START, END)
    pages = PdfReader(BytesIO(report.content)).pages
    assert len(pages) > 1
    text = " ".join(page.extract_text() for page in pages)
    assert "Total de acessos: 150" in text
    rows = []
    for page in pages:
        content = page.extract_text()
        if "Usuário proprietário" in content:
            table = content.split("Usuário proprietário")[1].split("Por operação")[0]
            rows.extend(
                (int(user), int(count))
                for user, count in re.findall(r"\b(\d+)\s+(\d+)\b", table)
            )
    assert rows == [(user_id, 1) for user_id in range(1, 151)]
    assert all("Usuário proprietário" in page.extract_text() for page in pages[:-1])
    assert all(
        f"Página {index}" in page.extract_text() for index, page in enumerate(pages, 1)
    )
