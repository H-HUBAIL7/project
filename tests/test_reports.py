from datetime import date, timedelta

from sqlalchemy import select

from app import models as m
from app import reports

from .support import DatabaseTestCase


class AchievementTests(DatabaseTestCase):
    def test_averages_meet_threshold(self) -> None:
        rows = reports.achievement(self.session, min_average="70")
        self.assertTrue(rows)
        self.assertTrue(all(r["Average"] >= 70 for r in rows))

    def test_sorted_by_average_descending(self) -> None:
        averages = [
            r["Average"] for r in reports.achievement(self.session)
        ]
        self.assertEqual(averages, sorted(averages, reverse=True))

    def test_only_final_year_students(self) -> None:
        duration = dict(
            self.session.execute(
                select(m.Program.name, m.Program.duration_years)
            ).all()
        )
        for row in reports.achievement(self.session, min_average="0"):
            self.assertEqual(row["Year"], duration[row["Programme"]])

    def test_three_year_degree_finalists_included(self) -> None:
        rows = reports.achievement(self.session, min_average="0")
        self.assertIn(3, {r["Year"] for r in rows})

    def test_one_year_masters_finalists_included(self) -> None:
        rows = reports.achievement(self.session, min_average="0")
        self.assertIn(1, {r["Year"] for r in rows})


class StudentReportTests(DatabaseTestCase):
    def test_unregistered_students_have_no_enrolment(self) -> None:
        rows = reports.student_report(
            self.session, registration="not registered"
        )
        ids = [r["id"] for r in rows]
        self.assertTrue(ids)
        enrolled = self.session.scalar(
            select(m.Enrollment.id)
            .join(m.Student, m.Student.id == m.Enrollment.student_id)
            .where(
                m.Student.student_id.in_(ids),
                m.Enrollment.semester == "Spring",
                m.Enrollment.academic_year == "2025/26",
            )
        )
        self.assertIsNone(enrolled)

    def test_students_on_course_taught_by_lecturer(self) -> None:
        course = self.session.scalar(
            select(m.Course).where(m.Course.code == "CS101")
        )
        lecturer = course.lecturers[0]
        rows = reports.student_report(
            self.session, course="CS101", lecturer=lecturer.lecturer_id
        )
        self.assertTrue(rows)
        enrolled = set(
            self.session.scalars(
                select(m.Student.student_id)
                .join(m.Enrollment, m.Enrollment.student_id == m.Student.id)
                .where(m.Enrollment.course_id == course.id)
            )
        )
        self.assertEqual({r["id"] for r in rows}, enrolled)

    def test_lecturer_not_teaching_course_returns_nobody(self) -> None:
        course = self.session.scalar(
            select(m.Course).where(m.Course.code == "CS101")
        )
        outsider = self.session.scalar(
            select(m.Lecturer).where(
                m.Lecturer.id.not_in([x.id for x in course.lecturers])
            )
        )
        rows = reports.student_report(
            self.session, course="CS101", lecturer=outsider.lecturer_id
        )
        self.assertEqual(rows, [])

    def test_registered_and_unregistered_partition_everyone(self) -> None:
        yes = reports.student_report(self.session, registration="registered")
        no = reports.student_report(
            self.session, registration="not registered"
        )
        self.assertEqual(len(yes) + len(no), 800)


class CourseReportTests(DatabaseTestCase):
    def test_courses_taught_by_lecturers_in_department(self) -> None:
        rows = reports.course_report(self.session, department="Economics")
        self.assertTrue(rows)
        for row in rows:
            course = self.session.scalar(
                select(m.Course).where(m.Course.code == row["id"])
            )
            self.assertIn(
                "Economics",
                [x.department.name for x in course.lecturers],
            )

    def test_courses_taught_by_lecturer(self) -> None:
        rows = reports.course_report(self.session, lecturer="L0001")
        lecturer = self.session.scalar(
            select(m.Lecturer).where(m.Lecturer.lecturer_id == "L0001")
        )
        expected = {c.code for c in lecturer.courses}
        self.assertEqual({r["id"] for r in rows}, expected)


class PublicationReportTests(DatabaseTestCase):
    def test_respects_time_window(self) -> None:
        cutoff = date.today() - timedelta(days=360)
        rows = reports.publication_report(self.session, months="12")
        self.assertTrue(rows)
        self.assertTrue(all(r["Published"] >= cutoff for r in rows))

    def test_wider_window_returns_more(self) -> None:
        recent = reports.publication_report(self.session, months="12")
        older = reports.publication_report(self.session, months="48")
        self.assertGreater(len(older), len(recent))


class SupervisionTests(DatabaseTestCase):
    def test_sorted_by_projects_supervised(self) -> None:
        counts = [
            r["Projects"] for r in reports.supervision_report(self.session)
        ]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_expertise_filter_uses_lookup_table(self) -> None:
        rows = reports.supervision_report(
            self.session, area="Machine Learning"
        )
        self.assertTrue(rows)
        for row in rows:
            lecturer = self.session.scalar(
                select(m.Lecturer).where(
                    m.Lecturer.lecturer_id == row["id"]
                )
            )
            self.assertIn(
                "Machine Learning", [a.name for a in lecturer.expertise]
            )


class WorkforceTests(DatabaseTestCase):
    def test_staff_by_department(self) -> None:
        rows = reports.workforce_report(self.session, department="Physics")
        self.assertTrue(rows)
        self.assertTrue(all(r["Department"] == "Physics" for r in rows))

    def test_supervisors_of_student_employees_in_programme(self) -> None:
        programme = "BSc Computer Science"
        rows = reports.workforce_report(self.session, program=programme)
        expected = set(
            self.session.scalars(
                select(m.Staff.staff_id)
                .join(
                    m.StudentEmployment,
                    m.StudentEmployment.supervisor_staff_id == m.Staff.id,
                )
                .join(
                    m.Student,
                    m.Student.id == m.StudentEmployment.student_id,
                )
                .join(m.Program, m.Program.id == m.Student.program_id)
                .where(m.Program.name == programme)
            )
        )
        self.assertTrue(expected)
        self.assertEqual({r["id"] for r in rows}, expected)

    def test_student_staff_counts_are_accurate(self) -> None:
        total = sum(
            r["Student Staff"] for r in reports.workforce_report(self.session)
        )
        self.assertEqual(
            total,
            len(list(self.session.scalars(select(m.StudentEmployment)))),
        )

class MyReportTests(DatabaseTestCase):
    def test_active_courses_are_active(self) -> None:
        rows = reports.course_report(self.session, status="active")

        self.assertTrue(rows)
        self.assertTrue(
            all(row["status"] == "active" for row in rows)
        )

    def test_unknown_department_returns_no_courses(self) -> None:
        rows = reports.course_report(
            self.session,
            department="Does Not Exist",
        )

        self.assertEqual(rows, [])
    
    def test_physics_courses_match_department(self) -> None:
        rows = reports.course_report(
            self.session,
            department="Physics",
        )

        self.assertTrue(rows)

        for row in rows:
            course = self.session.scalar(
                select(m.Course).where(m.Course.code == row["id"])
            )
            lecturer_departments = [
                lecturer.department.name
                for lecturer in course.lecturers
            ]
            self.assertIn("Physics", lecturer_departments)