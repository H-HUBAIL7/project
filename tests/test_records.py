from sqlalchemy import func, select

from app import models as m
from app import records

from .support import DatabaseTestCase


def tab_labels(record: dict) -> list[str]:
    return [tab["label"] for tab in record["tabs"]]


class StudentRecordTests(DatabaseTestCase):
    def test_student_has_required_tabs(self) -> None:
        record = records.student_detail(self.session, "S00001")
        self.assertEqual(
            tab_labels(record), ["Info", "Enrolment", "Discipline", "Activity"]
        )

    def test_student_info_covers_brief_attributes(self) -> None:
        record = records.student_detail(self.session, "S00001")
        labels = {i["label"] for i in record["tabs"][0]["panel"]["items"]}
        expected = {
            "Student ID", "Name", "Date of birth", "Email", "Phone",
            "Programme", "Year of study", "Status",
        }
        self.assertTrue(expected <= labels)

    def test_advisor_contact_details_shown(self) -> None:
        record = records.student_detail(self.session, "S00001")
        labels = {i["label"] for i in record["tabs"][0]["panel"]["items"]}
        self.assertTrue(
            {"Advisor", "Advisor email", "Advisor phone", "Advisor office"}
            <= labels
        )

    def test_student_grade_count_matches_database(self) -> None:
        student = self.session.scalar(
            select(m.Student).where(m.Student.student_id == "S00001")
        )
        expected = self.session.scalar(
            select(func.count(m.Grade.id)).where(
                m.Grade.student_id == student.id
            )
        )
        record = records.student_detail(self.session, "S00001")
        grades = record["tabs"][1]["panel"]["blocks"][1]["body"]["rows"]
        self.assertEqual(len(grades), expected)

    def test_unknown_student_returns_none(self) -> None:
        self.assertIsNone(records.student_detail(self.session, "S99999"))


class StaffRecordTests(DatabaseTestCase):
    def test_lecturer_has_academic_tabs(self) -> None:
        record = records.staff_detail(self.session, "L0001")
        self.assertEqual(
            tab_labels(record), ["Info", "Teaching", "Research", "Service"]
        )

    def test_support_staff_has_different_tabs(self) -> None:
        record = records.staff_detail(self.session, "N0001")
        self.assertEqual(
            tab_labels(record), ["Info", "Emergency", "Supervision"]
        )

    def test_unknown_staff_returns_none(self) -> None:
        self.assertIsNone(records.staff_detail(self.session, "X0000"))


class OtherRecordTests(DatabaseTestCase):
    def test_course_enrolled_count_matches(self) -> None:
        course = self.session.scalar(
            select(m.Course).where(m.Course.code == "CS101")
        )
        expected = self.session.scalar(
            select(func.count(m.Enrollment.id)).where(
                m.Enrollment.course_id == course.id
            )
        )
        record = records.course_detail(self.session, "CS101")
        self.assertEqual(record["stats"][0]["value"], expected)

    def test_programme_record(self) -> None:
        record = records.program_detail(
            self.session, "BSc Computer Science"
        )
        self.assertEqual(record["subtitle"], "BSc")

    def test_department_record(self) -> None:
        record = records.department_detail(self.session, "Physics")
        self.assertEqual(
            tab_labels(record), ["Info", "People", "Courses", "Research"]
        )

    def test_project_record_totals_funding(self) -> None:
        record = records.project_detail(self.session, "1")
        rows = record["tabs"][1]["panel"]["rows"]
        total = sum(float(r["Amount"]) for r in rows)
        self.assertEqual(record["stats"][0]["value"], f"£{total:,.0f}")
