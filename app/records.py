from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from .models import (
    Committee,
    CommitteeMembership,
    Course,
    CourseMaterial,
    CourseSchedule,
    Department,
    DisciplinaryRecord,
    Enrollment,
    Grade,
    Lecturer,
    OrganisationMembership,
    Program,
    ProgramRequirement,
    ProjectFunding,
    ProjectMember,
    Publication,
    Qualification,
    ResearchArea,
    ResearchGroup,
    ResearchProject,
    Staff,
    Student,
    StudentEmployment,
    StudentOrganisation,
    course_lecturers,
    lecturer_expertise,
    publication_authors,
)

Rows = list[dict[str, Any]]


def _rows(session: Session, statement: Select) -> Rows:
    return [dict(row) for row in session.execute(statement).mappings()]


def _table(columns: list[str], rows: Rows) -> dict[str, Any]:
    return {"kind": "table", "columns": columns, "rows": rows}


def _fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    return {
        "kind": "fields",
        "items": [{"label": k, "value": v} for k, v in pairs],
    }


def _age(born: date | None) -> str:
    if not born:
        return ""
    today = date.today()
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return f"{born.isoformat()} ({years})"


# --------------------------------------------------------------- students


def search_students(
    session: Session,
    q: str = "",
    program: str = "",
    year: str = "",
    status: str = "",
    min_average: str = "",
) -> Rows:
    average = func.round(func.avg(Grade.score), 1)
    statement = (
        select(
            Student.student_id.label("id"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
            average.label("Average"),
            Student.graduation_status.label("status"),
        )
        .outerjoin(Program, Program.id == Student.program_id)
        .outerjoin(Grade, Grade.student_id == Student.id)
        .group_by(Student.id)
        .order_by(Student.student_id)
    )
    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            or_(
                Student.name.ilike(pattern),
                Student.student_id.ilike(pattern),
                Student.email.ilike(pattern),
            )
        )
    if program:
        statement = statement.where(Program.name == program)
    if year:
        statement = statement.where(Student.year_of_study == int(year))
    if status:
        statement = statement.where(Student.graduation_status == status)
    if min_average:
        statement = statement.having(average >= float(min_average))
    return _rows(session, statement)


def student_detail(
    session: Session, student_id: str
) -> dict[str, Any] | None:
    student = session.scalar(
        select(Student).where(Student.student_id == student_id)
    )
    if student is None:
        return None

    advisor = student.advisor
    average = session.scalar(
        select(func.round(func.avg(Grade.score), 1)).where(
            Grade.student_id == student.id
        )
    )

    enrolment = _rows(
        session,
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Enrollment.semester.label("Semester"),
            Enrollment.academic_year.label("Year"),
            Course.credits.label("Credits"),
        )
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.academic_year, Course.code),
    )

    grades = _rows(
        session,
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Grade.score.label("Grade"),
            Grade.semester.label("Semester"),
            Grade.academic_year.label("Year"),
        )
        .join(Course, Course.id == Grade.course_id)
        .where(Grade.student_id == student.id)
        .order_by(Grade.score.desc()),
    )

    discipline = _rows(
        session,
        select(
            DisciplinaryRecord.incident_date.label("Date"),
            DisciplinaryRecord.details.label("Details"),
            DisciplinaryRecord.outcome.label("Outcome"),
        )
        .where(DisciplinaryRecord.student_id == student.id)
        .order_by(DisciplinaryRecord.incident_date.desc()),
    )

    societies = _rows(
        session,
        select(
            StudentOrganisation.name.label("Organisation"),
            StudentOrganisation.category.label("Category"),
            OrganisationMembership.role.label("Role"),
            OrganisationMembership.joined_on.label("Joined"),
        )
        .join(
            OrganisationMembership,
            OrganisationMembership.organisation_id == StudentOrganisation.id,
        )
        .where(OrganisationMembership.student_id == student.id)
        .order_by(StudentOrganisation.name),
    )

    projects = _rows(
        session,
        select(
            ResearchProject.title.label("Project"),
            ProjectMember.role.label("Role"),
            ResearchProject.status.label("Status"),
        )
        .join(
            ProjectMember,
            ProjectMember.project_id == ResearchProject.id,
        )
        .where(ProjectMember.student_id == student.id),
    )

    jobs = _rows(
        session,
        select(
            StudentEmployment.job_title.label("Role"),
            Staff.name.label("Supervisor"),
            StudentEmployment.hours_per_week.label("Hours"),
            StudentEmployment.start_date.label("Started"),
        )
        .join(Staff, Staff.id == StudentEmployment.supervisor_staff_id)
        .where(StudentEmployment.student_id == student.id),
    )

    return {
        "title": student.name,
        "subtitle": student.student_id,
        "status": student.graduation_status,
        "stats": [
            {"label": "Average", "value": average or "-"},
            {"label": "Year", "value": student.year_of_study},
            {"label": "Courses", "value": len(grades)},
            {"label": "Records", "value": len(discipline)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Student ID", student.student_id),
                        ("Name", student.name),
                        ("Date of birth", _age(student.date_of_birth)),
                        ("Email", student.email),
                        ("Phone", student.phone),
                        ("Address", student.address),
                        ("Programme", student.program.name
                         if student.program else None),
                        ("Degree", student.program.degree_awarded
                         if student.program else None),
                        ("Year of study", student.year_of_study),
                        ("Status", student.graduation_status),
                        ("Advisor", advisor.name if advisor else None),
                        ("Advisor email", advisor.email if advisor else None),
                    ]
                ),
            },
            {
                "id": "enrolment",
                "label": "Enrolment",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Registrations",
                            "body": _table(
                                ["Code", "Course", "Semester", "Year",
                                 "Credits"],
                                enrolment,
                            ),
                        },
                        {
                            "heading": "Grades",
                            "body": _table(
                                ["Code", "Course", "Grade", "Semester",
                                 "Year"],
                                grades,
                            ),
                        },
                    ],
                },
            },
            {
                "id": "discipline",
                "label": "Discipline",
                "count": len(discipline),
                "panel": _table(["Date", "Details", "Outcome"], discipline),
            },
            {
                "id": "activity",
                "label": "Activity",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Organisations",
                            "body": _table(
                                ["Organisation", "Category", "Role",
                                 "Joined"],
                                societies,
                            ),
                        },
                        {
                            "heading": "Research",
                            "body": _table(
                                ["Project", "Role", "Status"], projects
                            ),
                        },
                        {
                            "heading": "Employment",
                            "body": _table(
                                ["Role", "Supervisor", "Hours", "Started"],
                                jobs,
                            ),
                        },
                    ],
                },
            },
        ],
    }


# ------------------------------------------------------------------ staff


def search_staff(
    session: Session,
    q: str = "",
    kind: str = "",
    department: str = "",
    job_title: str = "",
    status: str = "",
) -> Rows:
    academic = (
        select(
            Lecturer.lecturer_id.label("id"),
            Lecturer.name.label("Name"),
            func.coalesce(Department.name, "").label("Department"),
            Lecturer.academic_title.label("Role"),
        )
        .outerjoin(Department, Department.id == Lecturer.department_id)
    )
    support = (
        select(
            Staff.staff_id.label("id"),
            Staff.name.label("Name"),
            func.coalesce(Department.name, "").label("Department"),
            Staff.job_title.label("Role"),
        )
        .outerjoin(Department, Department.id == Staff.department_id)
    )

    if q:
        pattern = f"%{q}%"
        academic = academic.where(
            or_(Lecturer.name.ilike(pattern),
                Lecturer.lecturer_id.ilike(pattern))
        )
        support = support.where(
            or_(Staff.name.ilike(pattern), Staff.staff_id.ilike(pattern))
        )
    if department:
        academic = academic.where(Department.name == department)
        support = support.where(Department.name == department)
    if job_title:
        academic = academic.where(Lecturer.academic_title == job_title)
        support = support.where(Staff.job_title == job_title)
    if status:
        wanted = status == "active"
        academic = academic.where(Lecturer.active.is_(wanted))
        support = support.where(Staff.active.is_(wanted))

    rows: Rows = []
    if kind != "Non-academic":
        for row in _rows(session, academic.order_by(Lecturer.lecturer_id)):
            row["Type"] = "Academic"
            rows.append(row)
    if kind != "Academic":
        for row in _rows(session, support.order_by(Staff.staff_id)):
            row["Type"] = "Non-academic"
            rows.append(row)

    flags = dict(
        session.execute(
            select(Lecturer.lecturer_id, Lecturer.active)
        ).all()
    )
    flags.update(
        dict(session.execute(select(Staff.staff_id, Staff.active)).all())
    )
    for row in rows:
        row["status"] = "active" if flags.get(row["id"]) else "inactive"
    return sorted(rows, key=lambda r: r["id"])


def _lecturer_detail(session: Session, lecturer: Lecturer) -> dict[str, Any]:
    teaching = _rows(
        session,
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Course.level.label("Level"),
            Course.credits.label("Credits"),
        )
        .join(course_lecturers, course_lecturers.c.course_id == Course.id)
        .where(course_lecturers.c.lecturer_id == lecturer.id)
        .order_by(Course.code),
    )
    advisees = _rows(
        session,
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Program.name.label("Programme"),
            Student.year_of_study.label("Year"),
        )
        .outerjoin(Program, Program.id == Student.program_id)
        .where(Student.advisor_id == lecturer.id)
        .order_by(Student.name),
    )
    publications = _rows(
        session,
        select(
            Publication.published_on.label("Published"),
            Publication.title.label("Title"),
            Publication.venue.label("Venue"),
            Publication.publication_type.label("Type"),
        )
        .join(
            publication_authors,
            publication_authors.c.publication_id == Publication.id,
        )
        .where(publication_authors.c.lecturer_id == lecturer.id)
        .order_by(Publication.published_on.desc()),
    )
    projects = _rows(
        session,
        select(
            ResearchProject.title.label("Project"),
            ResearchProject.status.label("Status"),
            ProjectMember.role.label("Role"),
        )
        .join(
            ProjectMember, ProjectMember.project_id == ResearchProject.id
        )
        .where(ProjectMember.lecturer_id == lecturer.id),
    )
    led = _rows(
        session,
        select(
            ResearchProject.title.label("Project"),
            ResearchProject.status.label("Status"),
            ResearchProject.start_date.label("Start"),
        ).where(
            ResearchProject.principal_investigator_id == lecturer.id
        ),
    )
    committees = _rows(
        session,
        select(
            Committee.name.label("Committee"),
            CommitteeMembership.role.label("Role"),
            Committee.remit.label("Remit"),
        )
        .join(
            CommitteeMembership,
            CommitteeMembership.committee_id == Committee.id,
        )
        .where(CommitteeMembership.lecturer_id == lecturer.id),
    )
    quals = _rows(
        session,
        select(
            Qualification.award.label("Award"),
            Qualification.subject.label("Subject"),
            Qualification.institution.label("Institution"),
            Qualification.year_awarded.label("Year"),
        )
        .where(Qualification.lecturer_id == lecturer.id)
        .order_by(Qualification.year_awarded.desc()),
    )
    group = session.scalar(
        select(ResearchGroup).where(
            ResearchGroup.head_lecturer_id == lecturer.id
        )
    )

    return {
        "title": lecturer.name,
        "subtitle": f"{lecturer.lecturer_id} · {lecturer.academic_title}",
        "status": "active" if lecturer.active else "inactive",
        "stats": [
            {"label": "Courses", "value": len(teaching)},
            {"label": "Advisees", "value": len(advisees)},
            {"label": "Publications", "value": len(publications)},
            {"label": "Projects led", "value": len(led)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Details",
                            "body": _fields(
                                [
                                    ("Lecturer ID", lecturer.lecturer_id),
                                    ("Name", lecturer.name),
                                    ("Title", lecturer.academic_title),
                                    ("Department", lecturer.department.name
                                     if lecturer.department else None),
                                    ("Email", lecturer.email),
                                    ("Phone", lecturer.phone),
                                    ("Office", lecturer.office),
                                    ("Appointed", lecturer.appointed_on),
                                    ("Heads", group.name if group else None),
                                    ("Expertise", ", ".join(
                                        a.name for a in lecturer.expertise
                                    )),
                                    ("Research interests", ", ".join(
                                        a.name
                                        for a in lecturer.research_interests
                                    )),
                                ]
                            ),
                        },
                        {
                            "heading": "Qualifications",
                            "body": _table(
                                ["Award", "Subject", "Institution", "Year"],
                                quals,
                            ),
                        },
                    ],
                },
            },
            {
                "id": "teaching",
                "label": "Teaching",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Courses",
                            "body": _table(
                                ["Code", "Course", "Level", "Credits"],
                                teaching,
                            ),
                        },
                        {
                            "heading": "Advisees",
                            "body": _table(
                                ["Student ID", "Name", "Programme", "Year"],
                                advisees,
                            ),
                        },
                    ],
                },
            },
            {
                "id": "research",
                "label": "Research",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Principal investigator",
                            "body": _table(
                                ["Project", "Status", "Start"], led
                            ),
                        },
                        {
                            "heading": "Member",
                            "body": _table(
                                ["Project", "Status", "Role"], projects
                            ),
                        },
                        {
                            "heading": "Publications",
                            "body": _table(
                                ["Published", "Title", "Venue", "Type"],
                                publications,
                            ),
                        },
                    ],
                },
            },
            {
                "id": "service",
                "label": "Service",
                "panel": _table(
                    ["Committee", "Role", "Remit"], committees
                ),
            },
        ],
    }


def _support_detail(session: Session, member: Staff) -> dict[str, Any]:
    supervised = _rows(
        session,
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            StudentEmployment.job_title.label("Role"),
            StudentEmployment.hours_per_week.label("Hours"),
        )
        .join(Student, Student.id == StudentEmployment.student_id)
        .where(StudentEmployment.supervisor_staff_id == member.id)
        .order_by(Student.name),
    )
    return {
        "title": member.name,
        "subtitle": f"{member.staff_id} · {member.job_title}",
        "status": "active" if member.active else "inactive",
        "stats": [
            {"label": "Student staff", "value": len(supervised)},
            {"label": "Contract", "value": member.employment_type},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Staff ID", member.staff_id),
                        ("Name", member.name),
                        ("Job title", member.job_title),
                        ("Department", member.department.name
                         if member.department else None),
                        ("Employment type", member.employment_type),
                        ("Contract start", member.contract_start),
                        ("Contract end", member.contract_end or "Open-ended"),
                        ("Salary", f"{member.salary_currency} "
                                   f"{member.salary_amount:,.2f}"
                         if member.salary_amount else None),
                        ("Status", "Active" if member.active else "Inactive"),
                    ]
                ),
            },
            {
                "id": "emergency",
                "label": "Emergency",
                "panel": _fields(
                    [
                        ("Contact", member.emergency_contact_name),
                        ("Phone", member.emergency_contact_phone),
                        ("Relationship", member.emergency_contact_relation),
                    ]
                ),
            },
            {
                "id": "supervision",
                "label": "Supervision",
                "count": len(supervised),
                "panel": _table(
                    ["Student ID", "Name", "Role", "Hours"], supervised
                ),
            },
        ],
    }


def staff_detail(session: Session, staff_id: str) -> dict[str, Any] | None:
    lecturer = session.scalar(
        select(Lecturer).where(Lecturer.lecturer_id == staff_id)
    )
    if lecturer is not None:
        return _lecturer_detail(session, lecturer)
    member = session.scalar(select(Staff).where(Staff.staff_id == staff_id))
    if member is not None:
        return _support_detail(session, member)
    return None


# ---------------------------------------------------------------- courses


def search_courses(
    session: Session,
    q: str = "",
    department: str = "",
    level: str = "",
    status: str = "",
) -> Rows:
    enrolled = (
        select(func.count(Enrollment.id))
        .where(Enrollment.course_id == Course.id)
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
            Course.active.label("active"),
        )
        .outerjoin(Department, Department.id == Course.department_id)
        .order_by(Course.code)
    )
    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            or_(Course.name.ilike(pattern), Course.code.ilike(pattern))
        )
    if department:
        statement = statement.where(Department.name == department)
    if level:
        statement = statement.where(Course.level == level)
    if status:
        statement = statement.where(Course.active.is_(status == "active"))

    rows = _rows(session, statement)
    for row in rows:
        row["status"] = "active" if row.pop("active") else "retired"
    return rows


def course_detail(session: Session, code: str) -> dict[str, Any] | None:
    course = session.scalar(select(Course).where(Course.code == code))
    if course is None:
        return None

    roster = _rows(
        session,
        select(
            Student.student_id.label("Student ID"),
            Student.name.label("Name"),
            Enrollment.semester.label("Semester"),
            Program.name.label("Programme"),
        )
        .join(Student, Student.id == Enrollment.student_id)
        .outerjoin(Program, Program.id == Student.program_id)
        .where(Enrollment.course_id == course.id)
        .order_by(Student.student_id),
    )
    average = session.scalar(
        select(func.round(func.avg(Grade.score), 1)).where(
            Grade.course_id == course.id
        )
    )
    schedule = _rows(
        session,
        select(
            CourseSchedule.day_of_week.label("Day"),
            CourseSchedule.start_time.label("Start"),
            CourseSchedule.end_time.label("End"),
            CourseSchedule.room.label("Room"),
        ).where(CourseSchedule.course_id == course.id),
    )
    materials = _rows(
        session,
        select(
            CourseMaterial.title.label("Title"),
            CourseMaterial.material_type.label("Type"),
            CourseMaterial.reference.label("Reference"),
            CourseMaterial.required.label("Required"),
        ).where(CourseMaterial.course_id == course.id),
    )
    programmes = _rows(
        session,
        select(
            Program.name.label("Programme"),
            ProgramRequirement.year_of_study.label("Year"),
            ProgramRequirement.mandatory.label("Mandatory"),
        )
        .join(Program, Program.id == ProgramRequirement.program_id)
        .where(ProgramRequirement.course_id == course.id)
        .order_by(Program.name),
    )

    return {
        "title": course.name,
        "subtitle": course.code,
        "status": "active" if course.active else "retired",
        "stats": [
            {"label": "Enrolled", "value": len(roster)},
            {"label": "Average", "value": average or "-"},
            {"label": "Credits", "value": course.credits},
            {"label": "Lecturers", "value": len(course.lecturers)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Code", course.code),
                        ("Name", course.name),
                        ("Description", course.description),
                        ("Department", course.department.name
                         if course.department else None),
                        ("Level", course.level),
                        ("Credits", course.credits),
                        ("Lecturers", ", ".join(
                            f"{x.name} ({x.lecturer_id})"
                            for x in course.lecturers
                        )),
                        ("Prerequisites", ", ".join(
                            f"{c.code} {c.name}"
                            for c in course.prerequisites
                        ) or "None"),
                        ("Status", "Active" if course.active else "Retired"),
                    ]
                ),
            },
            {
                "id": "delivery",
                "label": "Delivery",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Schedule",
                            "body": _table(
                                ["Day", "Start", "End", "Room"], schedule
                            ),
                        },
                        {
                            "heading": "Materials",
                            "body": _table(
                                ["Title", "Type", "Reference", "Required"],
                                materials,
                            ),
                        },
                        {
                            "heading": "Programmes",
                            "body": _table(
                                ["Programme", "Year", "Mandatory"], programmes
                            ),
                        },
                    ],
                },
            },
            {
                "id": "roster",
                "label": "Enrolment",
                "count": len(roster),
                "panel": _table(
                    ["Student ID", "Name", "Semester", "Programme"], roster
                ),
            },
        ],
    }


# -------------------------------------------------------------- programmes


def search_programs(
    session: Session, q: str = "", department: str = "", degree: str = ""
) -> Rows:
    enrolled = (
        select(func.count(Student.id))
        .where(Student.program_id == Program.id)
        .correlate(Program)
        .scalar_subquery()
    )
    statement = (
        select(
            Program.name.label("id"),
            Program.degree_awarded.label("Degree"),
            Program.duration_years.label("Years"),
            Department.name.label("Department"),
            enrolled.label("Students"),
        )
        .outerjoin(Department, Department.id == Program.department_id)
        .order_by(Program.name)
    )
    if q:
        statement = statement.where(Program.name.ilike(f"%{q}%"))
    if department:
        statement = statement.where(Department.name == department)
    if degree:
        statement = statement.where(Program.degree_awarded == degree)
    return _rows(session, statement)


def program_detail(session: Session, name: str) -> dict[str, Any] | None:
    program = session.scalar(select(Program).where(Program.name == name))
    if program is None:
        return None

    structure = _rows(
        session,
        select(
            ProgramRequirement.year_of_study.label("Year"),
            Course.code.label("Code"),
            Course.name.label("Course"),
            Course.credits.label("Credits"),
            ProgramRequirement.mandatory.label("Mandatory"),
        )
        .join(Course, Course.id == ProgramRequirement.course_id)
        .where(ProgramRequirement.program_id == program.id)
        .order_by(ProgramRequirement.year_of_study, Course.code),
    )
    cohort = _rows(
        session,
        select(
            Student.year_of_study.label("Year"),
            func.count(Student.id).label("Students"),
            func.sum(
                func.iif(Student.graduation_status == "active", 1, 0)
            ).label("Active"),
        )
        .where(Student.program_id == program.id)
        .group_by(Student.year_of_study)
        .order_by(Student.year_of_study),
    )
    total = session.scalar(
        select(func.count(Student.id)).where(
            Student.program_id == program.id
        )
    )

    return {
        "title": program.name,
        "subtitle": program.degree_awarded,
        "status": "active",
        "stats": [
            {"label": "Students", "value": total},
            {"label": "Duration", "value": f"{program.duration_years} yr"},
            {"label": "Courses", "value": len(structure)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Name", program.name),
                        ("Degree awarded", program.degree_awarded),
                        ("Duration", f"{program.duration_years} years"),
                        ("Department", program.department.name
                         if program.department else None),
                        ("Enrolled students", total),
                    ]
                ),
            },
            {
                "id": "structure",
                "label": "Structure",
                "panel": _table(
                    ["Year", "Code", "Course", "Credits", "Mandatory"],
                    structure,
                ),
            },
            {
                "id": "cohort",
                "label": "Cohort",
                "panel": _table(["Year", "Students", "Active"], cohort),
            },
        ],
    }


# ------------------------------------------------------------ departments


def search_departments(
    session: Session, q: str = "", faculty: str = ""
) -> Rows:
    courses = (
        select(func.count(Course.id))
        .where(Course.department_id == Department.id)
        .correlate(Department)
        .scalar_subquery()
    )
    academics = (
        select(func.count(Lecturer.id))
        .where(Lecturer.department_id == Department.id)
        .correlate(Department)
        .scalar_subquery()
    )
    support = (
        select(func.count(Staff.id))
        .where(Staff.department_id == Department.id)
        .correlate(Department)
        .scalar_subquery()
    )
    statement = select(
        Department.name.label("id"),
        Department.faculty.label("Faculty"),
        Department.building.label("Building"),
        courses.label("Courses"),
        academics.label("Academics"),
        support.label("Support"),
    ).order_by(Department.name)
    if q:
        statement = statement.where(Department.name.ilike(f"%{q}%"))
    if faculty:
        statement = statement.where(Department.faculty == faculty)
    return _rows(session, statement)


def department_detail(session: Session, name: str) -> dict[str, Any] | None:
    dept = session.scalar(select(Department).where(Department.name == name))
    if dept is None:
        return None

    staff_rows = _rows(
        session,
        select(
            Lecturer.lecturer_id.label("ID"),
            Lecturer.name.label("Name"),
            Lecturer.academic_title.label("Title"),
            Lecturer.email.label("Email"),
        )
        .where(Lecturer.department_id == dept.id)
        .order_by(Lecturer.name),
    )
    support_rows = _rows(
        session,
        select(
            Staff.staff_id.label("ID"),
            Staff.name.label("Name"),
            Staff.job_title.label("Job Title"),
            Staff.employment_type.label("Type"),
        )
        .where(Staff.department_id == dept.id)
        .order_by(Staff.name),
    )
    course_rows = _rows(
        session,
        select(
            Course.code.label("Code"),
            Course.name.label("Course"),
            Course.level.label("Level"),
            Course.credits.label("Credits"),
        )
        .where(Course.department_id == dept.id)
        .order_by(Course.code),
    )
    groups = _rows(
        session,
        select(
            ResearchGroup.name.label("Group"),
            Lecturer.name.label("Head"),
        )
        .outerjoin(Lecturer, Lecturer.id == ResearchGroup.head_lecturer_id)
        .where(ResearchGroup.department_id == dept.id),
    )
    students = session.scalar(
        select(func.count(Student.id))
        .join(Program, Program.id == Student.program_id)
        .where(Program.department_id == dept.id)
    )

    return {
        "title": dept.name,
        "subtitle": dept.faculty,
        "status": "active",
        "stats": [
            {"label": "Students", "value": students},
            {"label": "Academics", "value": len(staff_rows)},
            {"label": "Support", "value": len(support_rows)},
            {"label": "Courses", "value": len(course_rows)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Name", dept.name),
                        ("Faculty", dept.faculty),
                        ("Building", dept.building),
                        ("Research areas", ", ".join(
                            a.name for a in dept.research_areas
                        )),
                        ("Students", students),
                    ]
                ),
            },
            {
                "id": "people",
                "label": "People",
                "panel": {
                    "kind": "stack",
                    "blocks": [
                        {
                            "heading": "Academic staff",
                            "body": _table(
                                ["ID", "Name", "Title", "Email"], staff_rows
                            ),
                        },
                        {
                            "heading": "Non-academic staff",
                            "body": _table(
                                ["ID", "Name", "Job Title", "Type"],
                                support_rows,
                            ),
                        },
                    ],
                },
            },
            {
                "id": "courses",
                "label": "Courses",
                "panel": _table(
                    ["Code", "Course", "Level", "Credits"], course_rows
                ),
            },
            {
                "id": "research",
                "label": "Research",
                "panel": _table(["Group", "Head"], groups),
            },
        ],
    }


# ---------------------------------------------------------------- research


def search_research(
    session: Session, q: str = "", status: str = "", area: str = ""
) -> Rows:
    total = (
        select(func.coalesce(func.sum(ProjectFunding.amount), 0))
        .where(ProjectFunding.project_id == ResearchProject.id)
        .correlate(ResearchProject)
        .scalar_subquery()
    )
    members = (
        select(func.count(ProjectMember.id))
        .where(ProjectMember.project_id == ResearchProject.id)
        .correlate(ResearchProject)
        .scalar_subquery()
    )
    statement = (
        select(
            ResearchProject.id.label("id"),
            ResearchProject.title.label("Project"),
            Lecturer.name.label("Lead"),
            ResearchProject.start_date.label("Start"),
            members.label("Team"),
            func.round(total / 1000.0, 1).label("Funding k"),
            ResearchProject.status.label("status"),
        )
        .join(
            Lecturer,
            Lecturer.id == ResearchProject.principal_investigator_id,
        )
        .order_by(ResearchProject.title)
    )
    if q:
        statement = statement.where(ResearchProject.title.ilike(f"%{q}%"))
    if status:
        statement = statement.where(ResearchProject.status == status)
    if area:
        statement = statement.where(
            ResearchProject.title.ilike(f"{area}%")
        )
    return _rows(session, statement)


def project_detail(session: Session, project_id: str) -> dict[str, Any] | None:
    project = session.get(ResearchProject, int(project_id))
    if project is None:
        return None

    funding = _rows(
        session,
        select(
            ProjectFunding.funder.label("Funder"),
            ProjectFunding.grant_reference.label("Reference"),
            ProjectFunding.amount.label("Amount"),
            ProjectFunding.currency.label("Currency"),
        ).where(ProjectFunding.project_id == project.id),
    )
    team = _rows(
        session,
        select(
            func.coalesce(Lecturer.name, Student.name).label("Member"),
            func.coalesce(
                Lecturer.lecturer_id, Student.student_id
            ).label("ID"),
            ProjectMember.role.label("Role"),
        )
        .outerjoin(Lecturer, Lecturer.id == ProjectMember.lecturer_id)
        .outerjoin(Student, Student.id == ProjectMember.student_id)
        .where(ProjectMember.project_id == project.id),
    )
    outputs = _rows(
        session,
        select(
            Publication.published_on.label("Published"),
            Publication.title.label("Title"),
            Publication.venue.label("Venue"),
            Publication.publication_type.label("Type"),
        )
        .where(Publication.project_id == project.id)
        .order_by(Publication.published_on.desc()),
    )
    total = sum(float(row["Amount"] or 0) for row in funding)

    return {
        "title": project.title,
        "subtitle": project.principal_investigator.name,
        "status": project.status,
        "stats": [
            {"label": "Funding", "value": f"£{total:,.0f}"},
            {"label": "Team", "value": len(team)},
            {"label": "Outputs", "value": len(outputs)},
        ],
        "tabs": [
            {
                "id": "info",
                "label": "Info",
                "panel": _fields(
                    [
                        ("Title", project.title),
                        ("Principal investigator",
                         project.principal_investigator.name),
                        ("Status", project.status),
                        ("Start", project.start_date),
                        ("End", project.end_date),
                        ("Outcomes", project.outcomes),
                    ]
                ),
            },
            {
                "id": "funding",
                "label": "Funding",
                "panel": _table(
                    ["Funder", "Reference", "Amount", "Currency"], funding
                ),
            },
            {
                "id": "team",
                "label": "Team",
                "count": len(team),
                "panel": _table(["ID", "Member", "Role"], team),
            },
            {
                "id": "outputs",
                "label": "Outputs",
                "count": len(outputs),
                "panel": _table(
                    ["Published", "Title", "Venue", "Type"], outputs
                ),
            },
        ],
    }


def expertise_options(session: Session) -> list[str]:
    return [
        name
        for (name,) in session.execute(
            select(ResearchArea.name)
            .join(
                lecturer_expertise,
                lecturer_expertise.c.research_area_id == ResearchArea.id,
            )
            .distinct()
            .order_by(ResearchArea.name)
        ).all()
    ]
