from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.commands import (
    CountEntitiesCommand,
    CreateWorkoutCommand,
    DeleteWorkoutCommand,
    GenerateAccessReportCommand,
    GetWorkoutCommand,
    ListUsersCommand,
    ListWorkoutsCommand,
    RegisterUserCommand,
    UpdateWorkoutCommand,
)
from app.context import ApplicationContext
from app.facade import ApplicationContext as ReexportedContext
from app.facade import FacadeSingletonController
from app.main import create_app
from app.reports.domain import AccessReportRequest, GeneratedReport
from app.users.domain import User, UserRegistration, UserRole
from app.workouts.domain import (
    Workout,
    WorkoutNotFoundError,
    WorkoutRegistration,
    WorkoutUpdate,
)

START = datetime(2026, 11, 18, tzinfo=UTC)
REGISTRATION = UserRegistration("maria", "maria@example.com", UserRole.STUDENT, "x")
USER = User(1, "maria", "maria@example.com", UserRole.STUDENT, "hash")
WORKOUT = Workout(42, 1, "Peito", "Supino")
NEW_WORKOUT = WorkoutRegistration(1, "Peito", "Supino")
UPDATE = WorkoutUpdate("Costas", "Remada")
REPORT_REQUEST = AccessReportRequest(START, START + timedelta(days=1), "html")
REPORT = GeneratedReport(b"<html></html>", "text/html; charset=utf-8")

# (método da fachada, argumentos, comando esperado, serviço, método, retorno)
OPERATIONS = [
    (
        "register_user",
        (REGISTRATION,),
        RegisterUserCommand(REGISTRATION),
        "users",
        "add_user",
        USER,
    ),
    ("list_users", (), ListUsersCommand(), "users", "list_users", [USER]),
    (
        "create_workout",
        (NEW_WORKOUT,),
        CreateWorkoutCommand(NEW_WORKOUT),
        "workouts",
        "create_workout",
        WORKOUT,
    ),
    (
        "get_workout",
        (42,),
        GetWorkoutCommand(42),
        "workouts",
        "get_workout",
        WORKOUT,
    ),
    (
        "list_workouts",
        (),
        ListWorkoutsCommand(),
        "workouts",
        "list_workouts",
        [WORKOUT],
    ),
    (
        "update_workout",
        (42, UPDATE),
        UpdateWorkoutCommand(42, UPDATE),
        "workouts",
        "update_workout",
        WORKOUT,
    ),
    (
        "delete_workout",
        (42,),
        DeleteWorkoutCommand(42),
        "workouts",
        "delete_workout",
        None,
    ),
    (
        "generate_access_report",
        (REPORT_REQUEST,),
        GenerateAccessReportCommand(REPORT_REQUEST),
        "reports",
        "generate",
        REPORT,
    ),
]
OPERATION_IDS = [operation[0] for operation in OPERATIONS]


def mock_context() -> ApplicationContext:
    return ApplicationContext(users=Mock(), workouts=Mock(), reports=Mock())


@pytest.mark.parametrize("operation", OPERATIONS, ids=OPERATION_IDS)
def test_facade_method_builds_and_executes_matching_command(monkeypatch, operation):
    method, arguments, expected_command, _, _, result = operation
    facade = FacadeSingletonController.get_instance()
    context = mock_context()
    calls = []

    def substitute(self, received_context, command):
        calls.append((self, received_context, command))
        return result

    monkeypatch.setattr(FacadeSingletonController, "execute", substitute)
    assert getattr(facade, method)(context, *arguments) is result
    assert calls == [(facade, context, expected_command)]
    assert vars(facade) == {}


@pytest.mark.parametrize("operation", OPERATIONS, ids=OPERATION_IDS)
def test_command_delegates_to_service_of_received_context(operation):
    _, arguments, command, service_name, service_method, result = operation
    context = mock_context()
    service = getattr(context, service_name)
    getattr(service, service_method).return_value = result
    assert command.execute(context) is result
    getattr(service, service_method).assert_called_once_with(*arguments)
    for other in {"users", "workouts", "reports"} - {service_name}:
        assert getattr(context, other).mock_calls == []


def test_count_command_sums_users_and_workouts_of_context():
    context = mock_context()
    context.users.count_users.return_value = 2
    context.workouts.count_workouts.return_value = 3
    assert CountEntitiesCommand().execute(context) == 5
    assert context.reports.mock_calls == []


def test_count_facade_method_uses_count_command(monkeypatch):
    facade = FacadeSingletonController.get_instance()
    context = mock_context()
    calls = []
    monkeypatch.setattr(
        FacadeSingletonController,
        "execute",
        lambda self, ctx, command: calls.append((ctx, command)) or 7,
    )
    assert facade.count_entities(context) == 7
    assert calls == [(context, CountEntitiesCommand())]


@pytest.mark.parametrize(
    "command",
    [operation[2] for operation in OPERATIONS] + [CountEntitiesCommand()],
    ids=[*OPERATION_IDS, "count_entities"],
)
def test_commands_are_immutable_and_do_not_store_context(command):
    assert all(
        field.type is not ApplicationContext and field.name != "context"
        for field in fields(command)
    )
    with pytest.raises(FrozenInstanceError):
        command.extra = 1
    assert command == type(command)(
        *(getattr(command, f.name) for f in fields(command))
    )


def test_facade_execute_runs_any_command_with_given_context():
    facade = FacadeSingletonController.get_instance()
    context = mock_context()
    command = Mock()
    command.execute.return_value = "resultado"
    assert facade.execute(context, command) == "resultado"
    command.execute.assert_called_once_with(context)
    assert vars(facade) == {}


def test_facade_propagates_domain_errors_from_commands():
    context = mock_context()
    context.workouts.get_workout.side_effect = WorkoutNotFoundError()
    with pytest.raises(WorkoutNotFoundError):
        FacadeSingletonController.get_instance().get_workout(context, 42)


def test_application_context_remains_importable_from_facade():
    assert ReexportedContext is ApplicationContext


@pytest.mark.parametrize("storage", ["memory", "sqlite"])
def test_same_command_runs_isolated_in_each_application_context(storage, tmp_path):
    facade = FacadeSingletonController.get_instance()
    first = create_app(storage=storage, database_path=tmp_path / "first.db")
    second = create_app(storage=storage, database_path=tmp_path / "second.db")
    with TestClient(first) as client:
        assert (
            client.post(
                "/users/",
                json={
                    "username": "maria",
                    "email": "maria@example.com",
                    "password": "Abcdef12",
                },
            ).status_code
            == 201
        )
    create = CreateWorkoutCommand(WorkoutRegistration(1, "Peito"))
    workout = facade.execute(first.state.context, create)
    assert workout == Workout(1, 1, "Peito", "")
    assert facade.execute(first.state.context, CountEntitiesCommand()) == 2
    assert facade.execute(second.state.context, CountEntitiesCommand()) == 0
    assert facade.execute(second.state.context, ListWorkoutsCommand()) == []
    updated = facade.execute(first.state.context, UpdateWorkoutCommand(1, UPDATE))
    assert updated == Workout(1, 1, "Costas", "Remada")
    report = facade.execute(
        first.state.context,
        GenerateAccessReportCommand(
            AccessReportRequest(
                datetime(2000, 1, 1, tzinfo=UTC),
                datetime(2100, 1, 1, tzinfo=UTC),
                "html",
            )
        ),
    )
    assert report.media_type.startswith("text/html")
    facade.execute(first.state.context, DeleteWorkoutCommand(1))
    with pytest.raises(WorkoutNotFoundError):
        facade.execute(first.state.context, GetWorkoutCommand(1))
    assert vars(facade) == {}
