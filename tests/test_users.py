import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class UserApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.client.close()

    def test_add_and_list_users_with_both_roles(self) -> None:
        self.assertEqual(self.client.get("/users/").json(), [])

        student = self.client.post(
            "/users/", json={"username": "maria", "email": "maria@example.com"}
        )
        admin = self.client.post(
            "/users/",
            json={"username": "ana", "email": "ana@example.com", "role": "admin"},
        )

        self.assertEqual(student.status_code, 201)
        self.assertEqual(admin.status_code, 201)
        self.assertEqual(
            self.client.get("/users/").json(),
            [
                {"id": 1, "username": "maria", "email": "maria@example.com", "role": "student"},
                {"id": 2, "username": "ana", "email": "ana@example.com", "role": "admin"},
            ],
        )

    def test_rejects_duplicate_username_or_email_without_case_sensitivity(self) -> None:
        self.client.post(
            "/users/", json={"username": "Maria", "email": "Maria@example.com"}
        )

        duplicate_username = self.client.post(
            "/users/", json={"username": " MARIA ", "email": "other@example.com"}
        )
        duplicate_email = self.client.post(
            "/users/", json={"username": "other", "email": "maria@EXAMPLE.com"}
        )

        self.assertEqual(duplicate_username.status_code, 409)
        self.assertEqual(duplicate_email.status_code, 409)
        self.assertEqual(len(self.client.get("/users/").json()), 1)

    def test_rejects_invalid_input(self) -> None:
        for payload in (
            {"username": "   ", "email": "maria@example.com"},
            {"username": "maria", "email": "not-an-email"},
            {"username": "maria", "email": "maria@example.com", "role": "trainer"},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/users/", json=payload).status_code, 422)

        self.assertEqual(self.client.get("/users/").json(), [])

    def test_new_app_has_an_empty_collection(self) -> None:
        self.client.post(
            "/users/", json={"username": "maria", "email": "maria@example.com"}
        )

        with TestClient(create_app()) as another_client:
            self.assertEqual(another_client.get("/users/").json(), [])


if __name__ == "__main__":
    unittest.main()
