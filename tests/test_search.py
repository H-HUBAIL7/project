from sqlalchemy import select

from app import models as m
from app import records

from .support import DatabaseTestCase


class StudentSearchTests(DatabaseTestCase):
    def test_no_filters_returns_everyone(self) -> None:
        self.assertEqual(len(records.search_students(self.session)), 800)

    def test_search_by_id(self) -> None:
        rows = records.search_students(self.session, q="S00001")
        self.assertIn("S00001", [r["id"] for r in rows])

    def test_search_by_name_is_case_insensitive(self) -> None:
        name = records.search_students(self.session)[0]["Name"]
        rows = records.search_students(self.session, q=name.upper())
        self.assertIn(name, [r["Name"] for r in rows])

    def test_programme_filter(self) -> None:
        rows = records.search_students(
            self.session, program="BSc Physics"
        )
        self.assertTrue(rows)
        self.assertTrue(all(r["Programme"] == "BSc Physics" for r in rows))

    def test_year_filter(self) -> None:
        rows = records.search_students(self.session, year="2")
        self.assertTrue(rows)
        self.assertTrue(all(r["Year"] == 2 for r in rows))

    def test_status_filter(self) -> None:
        rows = records.search_students(self.session, status="withdrawn")
        self.assertTrue(rows)
        self.assertTrue(all(r["status"] == "withdrawn" for r in rows))

    def test_minimum_average_filter(self) -> None:
        rows = records.search_students(self.session, min_average="75")
        self.assertTrue(rows)
        self.assertTrue(all(r["Average"] >= 75 for r in rows))

    def test_filters_combine(self) -> None:
        rows = records.search_students(
            self.session, program="BSc Physics", year="1"
        )
        self.assertTrue(
            all(r["Programme"] == "BSc Physics" and r["Year"] == 1
                for r in rows)
        )

    def test_no_match_returns_empty(self) -> None:
        self.assertEqual(
            records.search_students(self.session, q="zzzzzz"), []
        )

    def test_injection_attempt_is_treated_as_text(self) -> None:
        rows = records.search_students(
            self.session, q="'; DROP TABLE students; --"
        )
        self.assertEqual(rows, [])
        self.assertEqual(len(records.search_students(self.session)), 800)


class StaffSearchTests(DatabaseTestCase):
    def test_returns_both_staff_types(self) -> None:
        types = {r["Type"] for r in records.search_staff(self.session)}
        self.assertEqual(types, {"Academic", "Non-academic"})

    def test_total_is_lecturers_plus_staff(self) -> None:
        self.assertEqual(len(records.search_staff(self.session)), 160)

    def test_academic_filter(self) -> None:
        rows = records.search_staff(self.session, kind="Academic")
        self.assertEqual(len(rows), 90)

    def test_department_filter(self) -> None:
        rows = records.search_staff(self.session, department="Physics")
        self.assertTrue(rows)
        self.assertTrue(all(r["Department"] == "Physics" for r in rows))

    def test_expertise_filter(self) -> None:
        rows = records.search_staff(self.session, area="Genomics")
        self.assertTrue(rows)
        for row in rows:
            lecturer = self.session.scalar(
                select(m.Lecturer).where(m.Lecturer.lecturer_id == row["id"])
            )
            self.assertIn("Genomics", [a.name for a in lecturer.expertise])

    def test_inactive_filter(self) -> None:
        rows = records.search_staff(self.session, status="inactive")
        self.assertTrue(rows)
        self.assertTrue(all(r["status"] == "inactive" for r in rows))


class OtherSearchTests(DatabaseTestCase):
    def test_course_retired_filter(self) -> None:
        rows = records.search_courses(self.session, status="retired")
        self.assertTrue(all(r["status"] == "retired" for r in rows))

    def test_course_level_filter(self) -> None:
        rows = records.search_courses(self.session, level="Level 3")
        self.assertTrue(rows)
        self.assertTrue(all(r["Level"] == "Level 3" for r in rows))

    def test_programme_department_filter(self) -> None:
        rows = records.search_programs(
            self.session, department="Computer Science"
        )
        self.assertEqual(len(rows), 3)

    def test_department_search(self) -> None:
        self.assertEqual(len(records.search_departments(self.session)), 8)

    def test_research_status_filter(self) -> None:
        rows = records.search_research(self.session, status="completed")
        self.assertTrue(rows)
        self.assertTrue(all(r["status"] == "completed" for r in rows))
