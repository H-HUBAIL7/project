import unittest

from fastapi.testclient import TestClient

from app.main import PAGES, app

from .support import ensure_database


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_database()
        cls.client = TestClient(app)

    def test_interface_is_served(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])

    def test_catalogue_names_university(self) -> None:
        data = self.client.get("/api/catalogue").json()
        self.assertEqual(data["university"], "Ashcombe University")

    def test_catalogue_lists_every_page(self) -> None:
        data = self.client.get("/api/catalogue").json()
        self.assertEqual(len(data["pages"]), len(PAGES))

    def test_every_page_responds(self) -> None:
        for page_id in PAGES:
            with self.subTest(page=page_id):
                response = self.client.get(f"/api/page/{page_id}")
                self.assertEqual(response.status_code, 200)

    def test_filters_are_applied(self) -> None:
        data = self.client.get(
            "/api/page/students", params={"year": "1"}
        ).json()
        self.assertTrue(all(r["Year"] == 1 for r in data["rows"]))

    def test_unknown_filters_are_ignored(self) -> None:
        response = self.client.get(
            "/api/page/students", params={"nonsense": "x"}
        )
        self.assertEqual(response.json()["count"], 800)

    def test_unknown_page_is_404(self) -> None:
        self.assertEqual(
            self.client.get("/api/page/nope").status_code, 404
        )

    def test_student_record_endpoint(self) -> None:
        response = self.client.get("/api/record/student/S00001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subtitle"], "S00001")

    def test_programme_name_with_spaces(self) -> None:
        response = self.client.get(
            "/api/record/program/BSc Computer Science"
        )
        self.assertEqual(response.status_code, 200)

    def test_unknown_record_is_404(self) -> None:
        self.assertEqual(
            self.client.get("/api/record/student/S99999").status_code, 404
        )

    def test_unknown_record_type_is_404(self) -> None:
        self.assertEqual(
            self.client.get("/api/record/nope/1").status_code, 404
        )
