from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import Select, and_, func, literal, or_, select
from sqlalchemy.orm import Session

from .models import (
    Committee,
    CommitteeMembership,
    Course,
    Department,
    Enrollment,
    Grade,
    Lecturer,
    Program,
    ProjectMember,
    Publication,
    ResearchArea,
    ResearchProject,
    Staff,
    Student,
    StudentEmployment,
    course_lecturers,
    lecturer_expertise,
    publication_authors,
)

Rows = list[dict[str, Any]]


def _rows(session: Session, statement: Select) -> Rows:
    return [dict(row) for row in session.execute(statement).mappings()]


def _tidy(rows: Rows, *columns: str) -> Rows:
    for row in rows:
        for column in columns:
            if isinstance(row.get(column), str):
                row[column] = ", ".join(
                    part for part in row[column].split(",") if part
                )
    return rows


def students_by_course_and_lecturer(
    session: Session, course_code: str, lecturer_id: str
) -> Rows:
    statement = (
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Enrollment.semester.label("Semester"),
            Enrollment.academic_year.label("Year"),
        )
        .join(Enrollment, Enrollment.student_id == Student.id)
        .join(Course, Course.id == Enrollment.course_id)
        .join(course_lecturers, course_lecturers.c.course_id == Course.id)
        .join(Lecturer, Lecturer.id == course_lecturers.c.lecturer_id)
        .where(Course.code == course_code)
        .where(Lecturer.lecturer_id == lecturer_id)
        .distinct()
        .order_by(Student.student_id)
    )
    return _rows(session, statement)


def final_year_high_achievers(
    session: Session, minimum_average: float = 70.0
) -> Rows:
    statement = (
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
            func.round(func.avg(Grade.score), 1).label("Average"),
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Program, Program.id == Student.program_id)
        .where(Student.year_of_study == Program.duration_years)
        .group_by(Student.id, Program.name)
        .having(func.avg(Grade.score) > minimum_average)
        .order_by(func.avg(Grade.score).desc())
    )
    return _rows(session, statement)


def unregistered_students(
    session: Session, semester: str, academic_year: str
) -> Rows:
    registered = select(Enrollment.student_id).where(
        Enrollment.semester == semester,
        Enrollment.academic_year == academic_year,
    )
    statement = (
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.graduation_status.label("Status"),
        )
        .outerjoin(Program, Program.id == Student.program_id)
        .where(Student.id.not_in(registered))
        .order_by(Student.student_id)
    )
    return _rows(session, statement)


def advisor_contact(session: Session, student_id: str) -> Rows:
    statement = (
        select(
            Student.name.label("Student"),
            Lecturer.lecturer_id.label("Advisor ID"),
            Lecturer.name.label("Advisor"),
            Lecturer.email.label("Email"),
            Lecturer.phone.label("Phone"),
            Lecturer.office.label("Office"),
        )
        .join(Lecturer, Lecturer.id == Student.advisor_id)
        .where(Student.student_id == student_id)
    )
    return _rows(session, statement)


def lecturers_by_expertise(session: Session, area: str) -> Rows:
    statement = (
        select(
            Lecturer.lecturer_id.label("Lecturer ID"),
            Lecturer.name.label("Name"),
            Department.name.label("Department"),
            ResearchArea.name.label("Expertise"),
        )
        .join(lecturer_expertise, lecturer_expertise.c.lecturer_id
              == Lecturer.id)
        .join(
            ResearchArea,
            ResearchArea.id == lecturer_expertise.c.research_area_id,
        )
        .outerjoin(Department, Department.id == Lecturer.department_id)
        .where(ResearchArea.name == area)
        .order_by(Lecturer.name)
    )
    return _rows(session, statement)


def courses_by_department(session: Session, department: str) -> Rows:
    lecturer_names = func.group_concat(Lecturer.name.distinct())
    statement = (
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Course.level.label("Level"),
            Course.credits.label("Credits"),
            lecturer_names.label("Lecturers"),
        )
        .join(Department, Department.id == Course.department_id)
        .outerjoin(course_lecturers, course_lecturers.c.course_id == Course.id)
        .outerjoin(Lecturer, Lecturer.id == course_lecturers.c.lecturer_id)
        .where(Department.name == department)
        .group_by(Course.id)
        .order_by(Course.code)
    )
    return _tidy(_rows(session, statement), "Lecturers")


def top_project_supervisors(session: Session, limit: int = 10) -> Rows:
    student_projects = (
        select(ProjectMember.project_id)
        .where(ProjectMember.student_id.is_not(None))
        .distinct()
        .scalar_subquery()
    )
    statement = (
        select(
            Lecturer.lecturer_id.label("Lecturer ID"),
            Lecturer.name.label("Name"),
            func.count(ResearchProject.id.distinct()).label("Projects"),
        )
        .join(
            ResearchProject,
            ResearchProject.principal_investigator_id == Lecturer.id,
        )
        .where(ResearchProject.id.in_(student_projects))
        .group_by(Lecturer.id)
        .order_by(func.count(ResearchProject.id.distinct()).desc())
        .limit(limit)
    )
    return _rows(session, statement)


def recent_publications(session: Session, months: int = 12) -> Rows:
    cutoff = date.today() - timedelta(days=30 * months)
    author_names = func.group_concat(Lecturer.name.distinct())
    statement = (
        select(
            Publication.published_on.label("Published"),
            Publication.title.label("Title"),
            Publication.venue.label("Venue"),
            Publication.publication_type.label("Type"),
            author_names.label("Authors"),
        )
        .join(
            publication_authors,
            publication_authors.c.publication_id == Publication.id,
        )
        .join(Lecturer, Lecturer.id == publication_authors.c.lecturer_id)
        .where(Publication.published_on >= cutoff)
        .group_by(Publication.id)
        .order_by(Publication.published_on.desc())
    )
    return _tidy(_rows(session, statement), "Authors")


def students_by_advisor(session: Session, lecturer_id: str) -> Rows:
    statement = (
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
        )
        .join(Lecturer, Lecturer.id == Student.advisor_id)
        .outerjoin(Program, Program.id == Student.program_id)
        .where(Lecturer.lecturer_id == lecturer_id)
        .order_by(Student.name)
    )
    return _rows(session, statement)


def staff_by_department(session: Session, department: str) -> Rows:
    statement = (
        select(
            Staff.staff_id.label("Staff ID"),
            Staff.name.label("Name"),
            Staff.job_title.label("Job Title"),
            Staff.employment_type.label("Type"),
        )
        .join(Department, Department.id == Staff.department_id)
        .where(Department.name == department)
        .order_by(Staff.name)
    )
    return _rows(session, statement)


def supervisors_of_student_employees(
    session: Session, program: str
) -> Rows:
    statement = (
        select(
            Staff.staff_id.label("Staff ID"),
            Staff.name.label("Supervisor"),
            Staff.job_title.label("Job Title"),
            func.count(StudentEmployment.id).label("Student Staff"),
        )
        .join(
            StudentEmployment,
            StudentEmployment.supervisor_staff_id == Staff.id,
        )
        .join(Student, Student.id == StudentEmployment.student_id)
        .join(Program, Program.id == Student.program_id)
        .where(Program.name == program)
        .group_by(Staff.id)
        .order_by(func.count(StudentEmployment.id).desc())
    )
    return _rows(session, statement)


def committee_membership(session: Session, committee: str) -> Rows:
    statement = (
        select(
            Lecturer.lecturer_id.label("Lecturer ID"),
            Lecturer.name.label("Name"),
            CommitteeMembership.role.label("Role"),
            Department.name.label("Department"),
        )
        .join(
            CommitteeMembership,
            CommitteeMembership.lecturer_id == Lecturer.id,
        )
        .join(Committee, Committee.id == CommitteeMembership.committee_id)
        .outerjoin(Department, Department.id == Lecturer.department_id)
        .where(Committee.name == committee)
        .order_by(CommitteeMembership.role)
    )
    return _rows(session, statement)


def project_funding_overview(session: Session) -> Rows:
    from .models import ProjectFunding

    statement = (
        select(
            ResearchProject.title.label("Project"),
            Lecturer.name.label("Principal Investigator"),
            ResearchProject.status.label("Status"),
            func.group_concat(ProjectFunding.funder.distinct()).label(
                "Funders"
            ),
            func.sum(ProjectFunding.amount).label("Total"),
        )
        .join(
            Lecturer,
            Lecturer.id == ResearchProject.principal_investigator_id,
        )
        .outerjoin(
            ProjectFunding,
            ProjectFunding.project_id == ResearchProject.id,
        )
        .group_by(ResearchProject.id)
        .order_by(ResearchProject.title)
    )
    return _tidy(_rows(session, statement), "Funders")


def search_people(session: Session, term: str) -> Rows:
    pattern = f"%{term}%"
    student_stmt = select(
        Student.student_id.label("ID"),
        Student.name.label("Name"),
        literal("Student").label("Type"),
        Student.email.label("Email"),
    ).where(or_(Student.name.ilike(pattern), Student.student_id.ilike(
        pattern)))
    lecturer_stmt = select(
        Lecturer.lecturer_id,
        Lecturer.name,
        literal("Lecturer"),
        Lecturer.email,
    ).where(
        or_(Lecturer.name.ilike(pattern), Lecturer.lecturer_id.ilike(pattern))
    )
    staff_stmt = select(
        Staff.staff_id,
        Staff.name,
        literal("Staff"),
        literal(None),
    ).where(or_(Staff.name.ilike(pattern), Staff.staff_id.ilike(pattern)))
    statement = student_stmt.union_all(lecturer_stmt, staff_stmt)
    return _rows(session, statement)


def course_prerequisite_chain(session: Session, course_code: str) -> Rows:
    from .models import course_prerequisites

    prereq = Course.__table__.alias("prereq")
    statement = (
        select(
            Course.code.label("Course"),
            prereq.c.code.label("Prerequisite"),
            prereq.c.name.label("Prerequisite Name"),
            prereq.c.credits.label("Credits"),
        )
        .join(
            course_prerequisites,
            course_prerequisites.c.course_id == Course.id,
        )
        .join(
            prereq,
            prereq.c.id == course_prerequisites.c.prerequisite_id,
        )
        .where(Course.code == course_code)
        .order_by(prereq.c.code)
    )
    return _rows(session, statement)


def student_record(session: Session, student_id: str) -> Rows:
    statement = (
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Enrollment.semester.label("Semester"),
            Enrollment.academic_year.label("Year"),
            Grade.score.label("Grade"),
        )
        .join(Student, Student.id == Enrollment.student_id)
        .join(Course, Course.id == Enrollment.course_id)
        .outerjoin(
            Grade,
            and_(
                Grade.student_id == Enrollment.student_id,
                Grade.course_id == Enrollment.course_id,
            ),
        )
        .where(Student.student_id == student_id)
        .order_by(Enrollment.academic_year, Course.code)
    )
    return _rows(session, statement)
