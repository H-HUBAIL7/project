from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import (
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


def achievement(
    session: Session,
    min_average: str = "70",
    year: str = "",
    program: str = "",
    status: str = "active",
    final_year_only: str = "yes",
) -> Rows:
    average = func.round(func.avg(Grade.score), 1)
    statement = (
        select(
            Student.student_id.label("id"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
            func.count(Grade.id).label("Courses"),
            average.label("Average"),
            Student.graduation_status.label("status"),
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Program, Program.id == Student.program_id)
        .group_by(Student.id)
        .having(average >= float(min_average or 0))
        .order_by(average.desc())
    )
    if final_year_only == "yes":
        statement = statement.where(
            Student.year_of_study == Program.duration_years
        )
    if year:
        statement = statement.where(Student.year_of_study == int(year))
    if program:
        statement = statement.where(Program.name == program)
    if status:
        statement = statement.where(Student.graduation_status == status)
    return _rows(session, statement)


def student_report(
    session: Session,
    status: str = "",
    program: str = "",
    year: str = "",
    registration: str = "",
    semester: str = "Spring",
    academic_year: str = "2025/26",
) -> Rows:
    registered = select(Enrollment.student_id).where(
        Enrollment.semester == semester,
        Enrollment.academic_year == academic_year,
    )
    statement = (
        select(
            Student.student_id.label("id"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
            Student.email.label("Email"),
            Student.graduation_status.label("status"),
        )
        .outerjoin(Program, Program.id == Student.program_id)
        .order_by(Student.student_id)
    )
    if status:
        statement = statement.where(Student.graduation_status == status)
    if program:
        statement = statement.where(Program.name == program)
    if year:
        statement = statement.where(Student.year_of_study == int(year))
    if registration == "registered":
        statement = statement.where(Student.id.in_(registered))
    elif registration == "not registered":
        statement = statement.where(Student.id.not_in(registered))
    return _rows(session, statement)


def course_report(
    session: Session,
    status: str = "",
    department: str = "",
    level: str = "",
    lecturer: str = "",
) -> Rows:
    enrolled = (
        select(func.count(Enrollment.id))
        .where(Enrollment.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    average = (
        select(func.round(func.avg(Grade.score), 1))
        .where(Grade.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    statement = (
        select(
            Course.code.label("id"),
            Course.name.label("Course"),
            Department.name.label("Department"),
            Course.level.label("Level"),
            Course.credits.label("Credits"),
            enrolled.label("Enrolled"),
            average.label("Average"),
            func.group_concat(Lecturer.name.distinct()).label("Lecturers"),
            Course.active.label("active"),
        )
        .outerjoin(Department, Department.id == Course.department_id)
        .outerjoin(course_lecturers, course_lecturers.c.course_id == Course.id)
        .outerjoin(Lecturer, Lecturer.id == course_lecturers.c.lecturer_id)
        .group_by(Course.id)
        .order_by(Course.code)
    )
    if status:
        statement = statement.where(Course.active.is_(status == "active"))
    if department:
        statement = statement.where(Department.name == department)
    if level:
        statement = statement.where(Course.level == level)
    if lecturer:
        statement = statement.where(Lecturer.lecturer_id == lecturer)

    rows = _tidy(_rows(session, statement), "Lecturers")
    for row in rows:
        row["status"] = "active" if row.pop("active") else "retired"
    return rows


def publication_report(
    session: Session,
    months: str = "12",
    kind: str = "",
    department: str = "",
) -> Rows:
    cutoff = date.today() - timedelta(days=int(float(months or 12) * 30))
    statement = (
        select(
            Publication.published_on.label("Published"),
            Publication.title.label("Title"),
            Publication.venue.label("Venue"),
            Publication.publication_type.label("Type"),
            func.group_concat(Lecturer.name.distinct()).label("Authors"),
            Publication.doi.label("DOI"),
        )
        .join(
            publication_authors,
            publication_authors.c.publication_id == Publication.id,
        )
        .join(Lecturer, Lecturer.id == publication_authors.c.lecturer_id)
        .outerjoin(Department, Department.id == Lecturer.department_id)
        .where(Publication.published_on >= cutoff)
        .group_by(Publication.id)
        .order_by(Publication.published_on.desc())
    )
    if kind:
        statement = statement.where(Publication.publication_type == kind)
    if department:
        statement = statement.where(Department.name == department)
    return _tidy(_rows(session, statement), "Authors")


def supervision_report(
    session: Session, department: str = "", area: str = ""
) -> Rows:
    student_projects = (
        select(ProjectMember.project_id)
        .where(ProjectMember.student_id.is_not(None))
        .distinct()
        .scalar_subquery()
    )
    led = (
        select(func.count(ResearchProject.id))
        .where(
            ResearchProject.principal_investigator_id == Lecturer.id,
            ResearchProject.id.in_(student_projects),
        )
        .correlate(Lecturer)
        .scalar_subquery()
    )
    advisees = (
        select(func.count(Student.id))
        .where(Student.advisor_id == Lecturer.id)
        .correlate(Lecturer)
        .scalar_subquery()
    )
    statement = (
        select(
            Lecturer.lecturer_id.label("id"),
            Lecturer.name.label("Name"),
            Lecturer.academic_title.label("Title"),
            Department.name.label("Department"),
            led.label("Projects"),
            advisees.label("Advisees"),
        )
        .outerjoin(Department, Department.id == Lecturer.department_id)
        .order_by(led.desc(), advisees.desc())
    )
    if department:
        statement = statement.where(Department.name == department)
    if area:
        statement = statement.where(
            Lecturer.id.in_(
                select(lecturer_expertise.c.lecturer_id)
                .join(
                    ResearchArea,
                    ResearchArea.id == lecturer_expertise.c.research_area_id,
                )
                .where(ResearchArea.name == area)
            )
        )
    return _rows(session, statement)


def workforce_report(
    session: Session,
    department: str = "",
    employment_type: str = "",
    status: str = "",
) -> Rows:
    supervised = (
        select(func.count(StudentEmployment.id))
        .where(StudentEmployment.supervisor_staff_id == Staff.id)
        .correlate(Staff)
        .scalar_subquery()
    )
    statement = (
        select(
            Staff.staff_id.label("id"),
            Staff.name.label("Name"),
            Staff.job_title.label("Job Title"),
            Department.name.label("Department"),
            Staff.employment_type.label("Contract"),
            Staff.contract_end.label("Ends"),
            supervised.label("Student Staff"),
            func.iif(Staff.active, "active", "inactive").label("status"),
        )
        .outerjoin(Department, Department.id == Staff.department_id)
        .order_by(Staff.name)
    )
    if department:
        statement = statement.where(Department.name == department)
    if employment_type:
        statement = statement.where(
            Staff.employment_type == employment_type
        )
    if status:
        statement = statement.where(Staff.active.is_(status == "active"))
    return _rows(session, statement)
