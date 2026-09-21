from datetime import date

from sqlalchemy.exc import IntegrityError

from app import models as m

from .support import DatabaseTestCase


class IntegrityTests(DatabaseTestCase):
    def test_duplicate_student_id_rejected(self) -> None:
        existing = self.session.query(m.Student).first()
        self.session.add(
            m.Student(student_id=existing.student_id, name="Duplicate")
        )
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_duplicate_lecturer_id_rejected(self) -> None:
        existing = self.session.query(m.Lecturer).first()
        self.session.add(
            m.Lecturer(lecturer_id=existing.lecturer_id, name="Duplicate")
        )
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_duplicate_course_code_rejected(self) -> None:
        existing = self.session.query(m.Course).first()
        self.session.add(m.Course(code=existing.code, name="Duplicate"))
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_duplicate_enrolment_rejected(self) -> None:
        existing = self.session.query(m.Enrollment).first()
        self.session.add(
            m.Enrollment(
                student_id=existing.student_id,
                course_id=existing.course_id,
                semester=existing.semester,
                academic_year=existing.academic_year,
            )
        )
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_lecturer_cannot_head_two_research_groups(self) -> None:
        group = self.session.query(m.ResearchGroup).filter(
            m.ResearchGroup.head_lecturer_id.is_not(None)
        ).first()
        self.session.add(
            m.ResearchGroup(
                name="Second group", head_lecturer_id=group.head_lecturer_id
            )
        )
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_student_cannot_join_organisation_twice(self) -> None:
        existing = self.session.query(m.OrganisationMembership).first()
        self.session.add(
            m.OrganisationMembership(
                student_id=existing.student_id,
                organisation_id=existing.organisation_id,
                joined_on=date(2025, 1, 1),
            )
        )
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_student_name_required(self) -> None:
        self.session.add(m.Student(student_id="S99999", name=None))
        with self.assertRaises(IntegrityError):
            self.session.flush()
