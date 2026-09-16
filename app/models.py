from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


course_lecturers = Table(
    "course_lecturers",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
    Column("lecturer_id", ForeignKey("lecturers.id"), primary_key=True),
)

department_research_areas = Table(
    "department_research_areas",
    Base.metadata,
    Column("department_id", ForeignKey("departments.id"), primary_key=True),
    Column(
        "research_area_id",
        ForeignKey("research_areas.id"),
        primary_key=True,
    ),
)

lecturer_expertise = Table(
    "lecturer_expertise",
    Base.metadata,
    Column("lecturer_id", ForeignKey("lecturers.id"), primary_key=True),
    Column(
        "research_area_id",
        ForeignKey("research_areas.id"),
        primary_key=True,
    ),
)

lecturer_research_interests = Table(
    "lecturer_research_interests",
    Base.metadata,
    Column("lecturer_id", ForeignKey("lecturers.id"), primary_key=True),
    Column(
        "research_area_id",
        ForeignKey("research_areas.id"),
        primary_key=True,
    ),
)

publication_authors = Table(
    "publication_authors",
    Base.metadata,
    Column("publication_id", ForeignKey("publications.id"), primary_key=True),
    Column("lecturer_id", ForeignKey("lecturers.id"), primary_key=True),
)

course_prerequisites = Table(
    "course_prerequisites",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
    Column(
        "prerequisite_id",
        ForeignKey("courses.id"),
        primary_key=True,
    ),
)


class ResearchArea(Base):
    __tablename__ = "research_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    faculty: Mapped[str | None] = mapped_column(String(120))
    building: Mapped[str | None] = mapped_column(String(60))
    research_areas: Mapped[list[ResearchArea]] = relationship(
        secondary=department_research_areas
    )


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    degree_awarded: Mapped[str | None] = mapped_column(String(100))
    duration_years: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    department: Mapped[Department | None] = relationship()
    requirements: Mapped[list[ProgramRequirement]] = relationship(
        back_populates="program"
    )


class ProgramRequirement(Base):
    __tablename__ = "program_requirements"
    __table_args__ = (UniqueConstraint("program_id", "course_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    year_of_study: Mapped[int]
    mandatory: Mapped[bool] = mapped_column(default=True)
    program: Mapped[Program] = relationship(back_populates="requirements")
    course: Mapped[Course] = relationship()


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    lecturer_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    office: Mapped[str | None] = mapped_column(String(60))
    academic_title: Mapped[str] = mapped_column(
        String(40), default="Lecturer"
    )
    appointed_on: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(default=True)
    department: Mapped[Department | None] = relationship()
    qualifications: Mapped[list[Qualification]] = relationship(
        back_populates="lecturer"
    )
    expertise: Mapped[list[ResearchArea]] = relationship(
        secondary=lecturer_expertise
    )
    research_interests: Mapped[list[ResearchArea]] = relationship(
        secondary=lecturer_research_interests
    )
    advisees: Mapped[list[Student]] = relationship(
        back_populates="advisor", foreign_keys="Student.advisor_id"
    )
    courses: Mapped[list[Course]] = relationship(
        secondary=course_lecturers, back_populates="lecturers"
    )
    publications: Mapped[list[Publication]] = relationship(
        secondary=publication_authors, back_populates="authors"
    )


class Qualification(Base):
    __tablename__ = "qualifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"))
    award: Mapped[str] = mapped_column(String(80))
    subject: Mapped[str | None] = mapped_column(String(150))
    institution: Mapped[str | None] = mapped_column(String(150))
    year_awarded: Mapped[int | None]
    lecturer: Mapped[Lecturer] = relationship(back_populates="qualifications")


class ResearchGroup(Base):
    __tablename__ = "research_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    head_lecturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("lecturers.id"), unique=True
    )
    department: Mapped[Department | None] = relationship()
    head: Mapped[Lecturer | None] = relationship()


class Committee(Base):
    __tablename__ = "committees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    remit: Mapped[str | None] = mapped_column(Text)


class CommitteeMembership(Base):
    __tablename__ = "committee_memberships"
    __table_args__ = (UniqueConstraint("committee_id", "lecturer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    committee_id: Mapped[int] = mapped_column(ForeignKey("committees.id"))
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"))
    role: Mapped[str | None] = mapped_column(String(60))
    committee: Mapped[Committee] = relationship()
    lecturer: Mapped[Lecturer] = relationship()


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    venue: Mapped[str | None] = mapped_column(String(200))
    publication_type: Mapped[str | None] = mapped_column(String(60))
    published_on: Mapped[date] = mapped_column(Date)
    doi: Mapped[str | None] = mapped_column(String(120))
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_projects.id")
    )
    authors: Mapped[list[Lecturer]] = relationship(
        secondary=publication_authors, back_populates="publications"
    )


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True)
    principal_investigator_id: Mapped[int] = mapped_column(
        ForeignKey("lecturers.id")
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="active")
    outcomes: Mapped[str | None] = mapped_column(Text)
    principal_investigator: Mapped[Lecturer] = relationship()
    funding: Mapped[list[ProjectFunding]] = relationship(
        back_populates="project"
    )
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project"
    )


class ProjectFunding(Base):
    __tablename__ = "project_funding"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id")
    )
    funder: Mapped[str] = mapped_column(String(180))
    grant_reference: Mapped[str | None] = mapped_column(String(80))
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    project: Mapped[ResearchProject] = relationship(back_populates="funding")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_projects.id")
    )
    lecturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("lecturers.id")
    )
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    role: Mapped[str | None] = mapped_column(String(60))
    project: Mapped[ResearchProject] = relationship(back_populates="members")
    lecturer: Mapped[Lecturer | None] = relationship()
    student: Mapped[Student | None] = relationship()


class StudentOrganisation(Base):
    __tablename__ = "student_organisations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    category: Mapped[str | None] = mapped_column(String(60))
    founded_year: Mapped[int | None]


class OrganisationMembership(Base):
    __tablename__ = "organisation_memberships"
    __table_args__ = (UniqueConstraint("student_id", "organisation_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("student_organisations.id")
    )
    role: Mapped[str | None] = mapped_column(String(60))
    joined_on: Mapped[date | None] = mapped_column(Date)
    student: Mapped[Student] = relationship(back_populates="organisations")
    organisation: Mapped[StudentOrganisation] = relationship()


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    year_of_study: Mapped[int | None]
    graduation_status: Mapped[str] = mapped_column(
        String(50), default="active"
    )
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("lecturers.id"))
    program: Mapped[Program | None] = relationship()
    advisor: Mapped[Lecturer | None] = relationship(
        back_populates="advisees", foreign_keys=[advisor_id]
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        back_populates="student"
    )
    grades: Mapped[list[Grade]] = relationship(back_populates="student")
    disciplinary_records: Mapped[list[DisciplinaryRecord]] = relationship(
        back_populates="student"
    )
    organisations: Mapped[list[OrganisationMembership]] = relationship(
        back_populates="student"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    level: Mapped[str | None] = mapped_column(String(30))
    credits: Mapped[int | None]
    active: Mapped[bool] = mapped_column(default=True)
    department: Mapped[Department | None] = relationship()
    lecturers: Mapped[list[Lecturer]] = relationship(
        secondary=course_lecturers, back_populates="courses"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        back_populates="course"
    )
    materials: Mapped[list[CourseMaterial]] = relationship(
        back_populates="course"
    )
    schedule: Mapped[list[CourseSchedule]] = relationship(
        back_populates="course"
    )
    prerequisites: Mapped[list[Course]] = relationship(
        secondary=course_prerequisites,
        primaryjoin=id == course_prerequisites.c.course_id,
        secondaryjoin=id == course_prerequisites.c.prerequisite_id,
    )


class CourseSchedule(Base):
    __tablename__ = "course_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    day_of_week: Mapped[str] = mapped_column(String(12))
    start_time: Mapped[str] = mapped_column(String(5))
    end_time: Mapped[str] = mapped_column(String(5))
    room: Mapped[str | None] = mapped_column(String(60))
    course: Mapped[Course] = relationship(back_populates="schedule")


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(250))
    material_type: Mapped[str | None] = mapped_column(String(60))
    reference: Mapped[str | None] = mapped_column(String(250))
    required: Mapped[bool] = mapped_column(default=False)
    course: Mapped[Course] = relationship(back_populates="materials")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "semester", "academic_year"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    semester: Mapped[str] = mapped_column(String(30))
    academic_year: Mapped[str] = mapped_column(String(20))
    student: Mapped[Student] = relationship(back_populates="enrollments")
    course: Mapped[Course] = relationship(back_populates="enrollments")


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    score: Mapped[float] = mapped_column(Float)
    semester: Mapped[str | None] = mapped_column(String(30))
    academic_year: Mapped[str | None] = mapped_column(String(20))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    student: Mapped[Student] = relationship(back_populates="grades")
    course: Mapped[Course] = relationship()


class DisciplinaryRecord(Base):
    __tablename__ = "disciplinary_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    incident_date: Mapped[date] = mapped_column(Date)
    details: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    student: Mapped[Student] = relationship(
        back_populates="disciplinary_records"
    )


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    job_title: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id")
    )
    employment_type: Mapped[str | None] = mapped_column(String(50))
    contract_start: Mapped[date | None] = mapped_column(Date)
    contract_end: Mapped[date | None] = mapped_column(Date)
    salary_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    salary_currency: Mapped[str] = mapped_column(String(3), default="GBP")
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50))
    emergency_contact_relation: Mapped[str | None] = mapped_column(String(60))
    active: Mapped[bool] = mapped_column(default=True)
    department: Mapped[Department | None] = relationship()


class StudentEmployment(Base):
    __tablename__ = "student_employment"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    supervisor_staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    job_title: Mapped[str] = mapped_column(String(120))
    hours_per_week: Mapped[float | None] = mapped_column(Float)
    start_date: Mapped[date | None] = mapped_column(Date)
    student: Mapped[Student] = relationship()
    supervisor: Mapped[Staff] = relationship()
