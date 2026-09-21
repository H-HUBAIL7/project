from sqlalchemy import inspect

from app.database import engine

from .support import DatabaseTestCase

REQUIRED_TABLES = {
    "students", "lecturers", "staff", "courses", "departments", "programs",
    "research_projects", "enrollments", "grades", "disciplinary_records",
    "qualifications", "research_areas", "lecturer_expertise",
    "lecturer_research_interests", "department_research_areas",
    "publications", "publication_authors", "project_funding",
    "project_members", "research_groups", "committees",
    "committee_memberships", "student_organisations",
    "organisation_memberships", "course_prerequisites", "course_materials",
    "course_schedule", "program_requirements", "course_lecturers",
    "student_employment",
}


class SchemaTests(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.inspector = inspect(engine)

    def columns(self, table: str) -> set[str]:
        return {c["name"] for c in self.inspector.get_columns(table)}

    def test_all_required_tables_exist(self) -> None:
        missing = REQUIRED_TABLES - set(self.inspector.get_table_names())
        self.assertEqual(missing, set())

    def test_grades_not_stored_on_student(self) -> None:
        self.assertNotIn("grades", self.columns("students"))

    def test_disciplinary_records_not_stored_on_student(self) -> None:
        self.assertNotIn("disciplinary_records", self.columns("students"))

    def test_qualifications_not_stored_on_lecturer(self) -> None:
        self.assertNotIn("qualifications", self.columns("lecturers"))

    def test_expertise_not_stored_on_lecturer(self) -> None:
        self.assertNotIn("expertise", self.columns("lecturers"))

    def test_research_interests_not_stored_on_lecturer(self) -> None:
        self.assertNotIn("research_interests", self.columns("lecturers"))

    def test_research_areas_not_stored_on_department(self) -> None:
        self.assertNotIn("research_areas", self.columns("departments"))

    def test_course_requirements_not_stored_on_program(self) -> None:
        self.assertNotIn("course_requirements", self.columns("programs"))

    def test_staff_emergency_contact_is_atomic(self) -> None:
        expected = {
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relation",
        }
        self.assertTrue(expected <= self.columns("staff"))

    def test_student_advisor_references_lecturer(self) -> None:
        keys = self.inspector.get_foreign_keys("students")
        targets = {
            (k["constrained_columns"][0], k["referred_table"]) for k in keys
        }
        self.assertIn(("advisor_id", "lecturers"), targets)

    def test_research_group_head_is_unique(self) -> None:
        unique = self.inspector.get_unique_constraints("research_groups")
        indexed = self.inspector.get_indexes("research_groups")
        columns = [c["column_names"] for c in unique] + [
            i["column_names"] for i in indexed if i.get("unique")
        ]
        self.assertIn(["head_lecturer_id"], columns)
