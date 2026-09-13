from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


course_lecturers = Table(
    "course_lecturers", Base.metadata,
    Column("course_id", ForeignKey("courses.id"), primary_key=True),
    Column("lecturer_id", ForeignKey("lecturers.id"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    faculty: Mapped[str | None] = mapped_column(String(120))
    research_areas: Mapped[str | None] = mapped_column(Text)


class Program(Base):
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    degree_awarded: Mapped[str | None] = mapped_column(String(100))
    duration_years: Mapped[int | None]
    course_requirements: Mapped[str | None] = mapped_column(Text)


class Lecturer(Base):
    __tablename__ = "lecturers"
    id: Mapped[int] = mapped_column(primary_key=True)
    lecturer_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    email: Mapped[str | None] = mapped_column(String(255))
    qualifications: Mapped[str | None] = mapped_column(Text)
    expertise: Mapped[str | None] = mapped_column(Text)
    research_interests: Mapped[str | None] = mapped_column(Text)
    department: Mapped[Department | None] = relationship()
    advisees: Mapped[list[Student]] = relationship(back_populates="advisor", foreign_keys="Student.advisor_id")
    courses: Mapped[list[Course]] = relationship(secondary=course_lecturers, back_populates="lecturers")


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"))
    year_of_study: Mapped[int | None]
    graduation_status: Mapped[str] = mapped_column(String(50), default="active")
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("lecturers.id"))
    program: Mapped[Program | None] = relationship()
    advisor: Mapped[Lecturer | None] = relationship(back_populates="advisees", foreign_keys=[advisor_id])
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="student")
    grades: Mapped[list[Grade]] = relationship(back_populates="student")
    disciplinary_records: Mapped[list[DisciplinaryRecord]] = relationship(back_populates="student")


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    level: Mapped[str | None] = mapped_column(String(30))
    credits: Mapped[int | None]
    schedule: Mapped[str | None] = mapped_column(Text)
    department: Mapped[Department | None] = relationship()
    lecturers: Mapped[list[Lecturer]] = relationship(secondary=course_lecturers, back_populates="courses")
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "semester", "academic_year"),)
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
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student: Mapped[Student] = relationship(back_populates="grades")


class DisciplinaryRecord(Base):
    __tablename__ = "disciplinary_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    incident_date: Mapped[date] = mapped_column(Date)
    details: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    student: Mapped[Student] = relationship(back_populates="disciplinary_records")


class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    job_title: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    contract_details: Mapped[str | None] = mapped_column(Text)
    salary_information: Mapped[str | None] = mapped_column(Text)
    emergency_contact: Mapped[str | None] = mapped_column(Text)
    department: Mapped[Department | None] = relationship()
