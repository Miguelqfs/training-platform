import pytest
from fastapi.testclient import TestClient

from app.main import create_app

USER = {"username": "maria", "email": "maria@example.com", "password": "Abcdef12"}


@pytest.fixture(params=["memory", "sqlite"])
def client(request, tmp_path):
    with TestClient(
        create_app(storage=request.param, database_path=tmp_path / "api.db")
    ) as client:
        yield client


@pytest.fixture
def populated(client):
    assert client.post("/users/", json=USER).status_code == 201
    return client


def test_crud_keeps_relationship_and_counts_both_roles(client):
    assert client.get("/statistics/entities").json() == {"total": 0}
    assert client.get("/workouts/").json() == []
    for username, role in [("maria", "student"), ("ana", "admin")]:
        response = client.post(
            "/users/",
            json={
                **USER,
                "username": username,
                "email": f"{username}@example.com",
                "role": role,
            },
        )
        assert response.status_code == 201
    users = client.get("/users/").json()
    workouts = []
    for user_id in (1, 1, 2):
        response = client.post(
            "/workouts/",
            json={
                "user_id": user_id,
                "name": "  Força 🏋️  ",
                "description": "  Segunda  ",
            },
        )
        assert response.status_code == 201
        workouts.append(response.json())
    assert workouts == [
        dict(id=i, user_id=u, name="Força 🏋️", description="Segunda")
        for i, u in ((1, 1), (2, 1), (3, 2))
    ]
    assert client.get("/workouts/").json() == workouts
    assert client.get("/statistics/entities").json() == {"total": 5}
    assert client.get("/workouts/1").json() == workouts[0]
    response = client.put(
        "/workouts/1", json={"name": " Costas ", "description": " remada "}
    )
    assert response.status_code == 200
    assert response.json() == dict(id=1, user_id=1, name="Costas", description="remada")
    response = client.put("/workouts/1", json={"name": "  Novo  "})
    assert response.status_code == 200
    assert response.json() == dict(id=1, user_id=1, name="Novo", description="")
    assert client.get("/statistics/entities").json() == {"total": 5}
    response = client.delete("/workouts/3")
    assert response.status_code == 204
    assert response.content == b""
    assert client.delete("/workouts/3").status_code == 404
    assert client.get("/workouts/3").status_code == 404
    assert client.put("/workouts/3", json={"name": "Ausente"}).status_code == 404
    assert client.get("/statistics/entities").json() == {"total": 4}
    assert (
        client.post("/workouts/", json={"user_id": 2, "name": "Novo"}).json()["id"] == 4
    )
    assert client.delete("/workouts/2").status_code == 204
    assert (
        client.post("/workouts/", json={"user_id": 1, "name": "Novo"}).json()["id"] == 5
    )
    assert [w["id"] for w in client.get("/workouts/").json()] == [1, 4, 5]
    assert client.get("/users/").json() == users


@pytest.mark.parametrize(
    "patch,field",
    [
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"name": "á" * 101}, "name"),
        ({"name": None}, "name"),
        ({"name": 3}, "name"),
        ({"name": True}, "name"),
        ({"name": []}, "name"),
        ({"description": "á" * 1001}, "description"),
        ({"description": None}, "description"),
        ({"description": 3}, "description"),
        ({"description": False}, "description"),
        ({"user_id": "1"}, "user_id"),
        ({"user_id": True}, "user_id"),
        ({"user_id": 1.0}, "user_id"),
        ({"user_id": 0}, "user_id"),
        ({"user_id": -1}, "user_id"),
        ({"user_id": None}, "user_id"),
        ({"id": 1}, "id"),
        ({"password": "sensitive-extra"}, "password"),
        ({"password_hash": "sensitive-extra"}, "password_hash"),
    ],
)
def test_invalid_create_identifies_field_without_writing_or_echoing(
    populated, patch, field
):
    response = populated.post(
        "/workouts/", json={"user_id": 1, "name": "Normal", **patch}
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", field] and e["type"] and e["msg"] for e in errors)
    assert all("input" not in e and "ctx" not in e for e in errors)
    assert "sensitive-extra" not in response.text
    assert populated.get("/workouts/").json() == []
    assert populated.get("/statistics/entities").json() == {"total": 1}


@pytest.mark.parametrize("body,field", [({}, "name"), ({"name": "Treino"}, "user_id")])
def test_required_fields(client, body, field):
    response = client.post("/workouts/", json=body)
    assert response.status_code == 422
    assert any(
        e["loc"] == ["body", field] and e["type"] == "missing"
        for e in response.json()["detail"]
    )
    assert client.get("/statistics/entities").json() == {"total": 0}


def test_boundaries_and_legitimate_text_equal_to_password(populated):
    for name, description in [
        ("a", ""),
        ("á" * 100, "ç" * 1000),
        (USER["password"], USER["password"]),
        ("Normal", "   "),
        ('Plano "; DROP TABLE users; --', "Texto parametrizado"),
    ]:
        response = populated.post(
            "/workouts/",
            json={"user_id": 1, "name": f" {name} ", "description": f" {description} "},
        )
        assert response.status_code == 201
        assert response.json() == dict(
            id=response.json()["id"],
            user_id=1,
            name=name.strip(),
            description=description.strip(),
        )
    for user in populated.get("/users/").json():
        assert set(user) == {"id", "username", "email", "role"}
    for workout in populated.get("/workouts/").json():
        assert set(workout) == {"id", "user_id", "name", "description"}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": ""},
        {"name": None},
        {"name": "x" * 101},
        {"name": "Novo", "description": None},
        {"name": "Novo", "description": 1},
        {"name": "Novo", "description": "x" * 1001},
        {"name": "Novo", "id": 1},
        {"name": "Novo", "user_id": 1},
        {"name": "Novo", "other": "sensitive-extra"},
    ],
)
def test_invalid_update_keeps_every_field(populated, body):
    previous = populated.post(
        "/workouts/", json={"user_id": 1, "name": "Anterior", "description": "Manter"}
    ).json()
    response = populated.put("/workouts/1", json=body)
    assert response.status_code == 422
    assert "sensitive-extra" not in response.text
    assert populated.get("/workouts/1").json() == previous
    assert populated.get("/statistics/entities").json() == {"total": 2}


@pytest.mark.parametrize("method", ["get", "put", "delete"])
@pytest.mark.parametrize("identifier", ["0", "-1", "abc", "1.2"])
def test_invalid_path_id_is_validation_error(client, method, identifier):
    kwargs = {"json": {"name": "Novo"}} if method == "put" else {}
    response = client.request(method, f"/workouts/{identifier}", **kwargs)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "workout_id"]


def test_missing_records_are_404_without_mutation(populated):
    response = populated.post("/workouts/", json={"user_id": 999, "name": "Treino"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Usuário não encontrado"}
    for method in ("get", "put", "delete"):
        kwargs = {"json": {"name": "Novo"}} if method == "put" else {}
        response = populated.request(method, "/workouts/999", **kwargs)
        assert response.status_code == 404
        assert response.json() == {"detail": "Treino não encontrado"}
    assert populated.get("/statistics/entities").json() == {"total": 1}


def test_openapi_describes_positive_ids_and_nonnegative_total(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for model in ("WorkoutCreate", "WorkoutResponse"):
        assert schemas[model]["properties"]["user_id"]["exclusiveMinimum"] == 0
    assert schemas["WorkoutResponse"]["properties"]["id"]["exclusiveMinimum"] == 0
    assert schemas["EntityCount"]["properties"]["total"]["minimum"] == 0
