from sqlalchemy import func, select

from app import models as m

from .support import DatabaseTestCase


class SeedDataTests(DatabaseTestCase):
    def count(self, model) -> int:
        return self.session.scalar(select(func.count()).select_from(model))

    def test_student_volume(self) -> None:
        self.assertEqual(self.count(m.Student), 800)

    def test_lecturer_volume(self) -> None:
        self.assertEqual(self.count(m.Lecturer), 90)

    def test_non_academic_staff_volume(self) -> None:
        self.assertEqual(self.count(m.Staff), 70)

    def test_every_student_has_a_programme(self) -> None:
        orphans = self.session.scalar(
            select(func.count(m.Student.id)).where(
                m.Student.program_id.is_(None)
            )
        )
        self.assertEqual(orphans, 0)

    def test_year_never_exceeds_programme_length(self) -> None:
        invalid = self.session.scalar(
            select(func.count(m.Student.id))
            .join(m.Program, m.Program.id == m.Student.program_id)
            .where(m.Student.year_of_study > m.Program.duration_years)
        )
        self.assertEqual(invalid, 0)

    def test_grades_within_range(self) -> None:
        low, high = self.session.execute(
            select(func.min(m.Grade.score), func.max(m.Grade.score))
        ).one()
        self.assertGreaterEqual(low, 0)
        self.assertLessEqual(high, 100)

    def test_student_statuses_are_varied(self) -> None:
        statuses = set(
            self.session.scalars(select(m.Student.graduation_status))
        )
        self.assertTrue(
            {"active", "graduated", "withdrawn", "suspended"} <= statuses
        )

    def test_every_course_has_a_lecturer(self) -> None:
        for course in self.session.scalars(select(m.Course)):
            self.assertTrue(course.lecturers, course.code)

    def test_prerequisites_are_lower_level(self) -> None:
        for course in self.session.scalars(select(m.Course)):
            level = int(course.level.split()[-1])
            for prereq in course.prerequisites:
                self.assertLess(int(prereq.level.split()[-1]), level)

    def test_advisor_in_same_department_as_programme(self) -> None:
        mismatched = self.session.scalar(
            select(func.count(m.Student.id))
            .join(m.Program, m.Program.id == m.Student.program_id)
            .join(m.Lecturer, m.Lecturer.id == m.Student.advisor_id)
            .where(m.Lecturer.department_id != m.Program.department_id)
        )
        self.assertEqual(mismatched, 0)

    def test_seed_is_repeatable(self) -> None:
        first = self.session.scalar(
            select(m.Student.name).where(m.Student.student_id == "S00001")
        )
        self.assertTrue(first)
        self.assertEqual(self.count(m.Student), 800)
