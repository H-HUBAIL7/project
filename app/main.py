from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from . import records, reports
from .database import get_session
from .models import (
    Course,
    Department,
    Lecturer,
    Program,
    Publication,
    ResearchArea,
    Staff,
    Student,
)

UNIVERSITY = "Ashcombe University"
STATIC = Path(__file__).parent / "static"

app = FastAPI(title=f"{UNIVERSITY} Records", version="3.0.0")


def text(name: str, label: str, placeholder: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "kind": "text",
        "placeholder": placeholder,
    }


def number(name: str, label: str, default: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "kind": "number",
        "default": default,
    }


def choice(
    name: str, label: str, source: str, default: str = ""
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "kind": "select",
        "source": source,
        "default": default,
    }


PAGES: dict[str, dict[str, Any]] = {
    "students": {
        "section": "Search",
        "label": "Students",
        "columns": ["id", "Name", "Programme", "Year", "Average"],
        "detail": "student",
        "filters": [
            text("q", "Name or ID", "Search"),
            choice("program", "Programme", "programs"),
            choice("year", "Year", "years"),
            choice("status", "Status", "student_status"),
            number("min_average", "Min average"),
        ],
        "run": records.search_students,
    },
    "staff": {
        "section": "Search",
        "label": "Staff",
        "columns": ["id", "Name", "Type", "Department", "Role"],
        "detail": "staff",
        "filters": [
            text("q", "Name or ID", "Search"),
            choice("kind", "Type", "staff_types"),
            choice("department", "Department", "departments"),
            choice("job_title", "Role", "roles"),
            choice("status", "Status", "activity"),
        ],
        "run": records.search_staff,
    },
    "courses": {
        "section": "Search",
        "label": "Courses",
        "columns": ["id", "Course", "Department", "Level", "Credits",
                    "Enrolled"],
        "detail": "course",
        "filters": [
            text("q", "Name or code", "Search"),
            choice("department", "Department", "departments"),
            choice("level", "Level", "levels"),
            choice("status", "Status", "course_status"),
        ],
        "run": records.search_courses,
    },
    "programmes": {
        "section": "Search",
        "label": "Programmes",
        "columns": ["id", "Degree", "Years", "Department", "Students"],
        "detail": "program",
        "filters": [
            text("q", "Name", "Search"),
            choice("department", "Department", "departments"),
            choice("degree", "Degree", "degrees"),
        ],
        "run": records.search_programs,
    },
    "departments": {
        "section": "Search",
        "label": "Departments",
        "columns": ["id", "Faculty", "Building", "Courses", "Academics",
                    "Support"],
        "detail": "department",
        "filters": [
            text("q", "Name", "Search"),
            choice("faculty", "Faculty", "faculties"),
        ],
        "run": records.search_departments,
    },
    "research": {
        "section": "Search",
        "label": "Research",
        "columns": ["Project", "Lead", "Start", "Team", "Funding k"],
        "detail": "project",
        "filters": [
            text("q", "Title", "Search"),
            choice("status", "Status", "project_status"),
            choice("area", "Area", "areas"),
        ],
        "run": records.search_research,
    },
    "achievement": {
        "section": "Reports",
        "label": "Achievement",
        "columns": ["id", "Name", "Programme", "Year", "Courses", "Average"],
        "detail": "student",
        "filters": [
            number("min_average", "Min average", "70"),
            choice("final_year_only", "Final year", "yes_no", "yes"),
            choice("program", "Programme", "programs"),
            choice("year", "Year", "years"),
            choice("status", "Status", "student_status", "active"),
        ],
        "run": reports.achievement,
    },
    "student-report": {
        "section": "Reports",
        "label": "Students",
        "columns": ["id", "Name", "Programme", "Year", "Email"],
        "detail": "student",
        "filters": [
            choice("status", "Status", "student_status"),
            choice("registration", "Registration", "registration"),
            choice("program", "Programme", "programs"),
            choice("year", "Year", "years"),
        ],
        "run": reports.student_report,
    },
    "course-report": {
        "section": "Reports",
        "label": "Courses",
        "columns": ["id", "Course", "Department", "Level", "Enrolled",
                    "Average", "Lecturers"],
        "detail": "course",
        "filters": [
            choice("status", "Status", "course_status"),
            choice("department", "Department", "departments"),
            choice("level", "Level", "levels"),
        ],
        "run": reports.course_report,
    },
    "publication-report": {
        "section": "Reports",
        "label": "Publications",
        "columns": ["Published", "Title", "Venue", "Type", "Authors"],
        "filters": [
            number("months", "Months back", "12"),
            choice("kind", "Type", "publication_types"),
            choice("department", "Department", "departments"),
        ],
        "run": reports.publication_report,
    },
    "supervision-report": {
        "section": "Reports",
        "label": "Supervision",
        "columns": ["id", "Name", "Title", "Department", "Projects",
                    "Advisees"],
        "detail": "staff",
        "filters": [
            choice("department", "Department", "departments"),
            choice("area", "Expertise", "expertise"),
        ],
        "run": reports.supervision_report,
    },
    "workforce-report": {
        "section": "Reports",
        "label": "Workforce",
        "columns": ["id", "Name", "Job Title", "Department", "Contract",
                    "Ends", "Student Staff"],
        "detail": "staff",
        "filters": [
            choice("department", "Department", "departments"),
            choice("employment_type", "Contract", "employment_types"),
            choice("status", "Status", "activity"),
        ],
        "run": reports.workforce_report,
    },
}

DETAILS: dict[str, Callable[..., Any]] = {
    "student": records.student_detail,
    "staff": records.staff_detail,
    "course": records.course_detail,
    "program": records.program_detail,
    "department": records.department_detail,
    "project": records.project_detail,
}


def options(db: Session) -> dict[str, list[str]]:
    def col(field) -> list[str]:
        return [
            value
            for (value,) in db.execute(
                select(distinct(field)).order_by(field)
            ).all()
            if value
        ]

    return {
        "programs": col(Program.name),
        "departments": col(Department.name),
        "faculties": col(Department.faculty),
        "degrees": col(Program.degree_awarded),
        "levels": col(Course.level),
        "areas": col(ResearchArea.name),
        "expertise": records.expertise_options(db),
        "publication_types": col(Publication.publication_type),
        "employment_types": col(Staff.employment_type),
        "roles": col(Lecturer.academic_title) + col(Staff.job_title),
        "years": ["1", "2", "3", "4"],
        "student_status": col(Student.graduation_status),
        "course_status": ["active", "retired"],
        "project_status": ["active", "completed", "proposed"],
        "staff_types": ["Academic", "Non-academic"],
        "activity": ["active", "inactive"],
        "registration": ["registered", "not registered"],
        "yes_no": ["yes", "no"],
    }


@app.get("/api/catalogue")
def catalogue(db: Session = Depends(get_session)) -> dict[str, Any]:
    pages = [
        {
            "id": key,
            "label": spec["label"],
            "section": spec["section"],
            "columns": spec["columns"],
            "detail": spec.get("detail"),
            "filters": spec["filters"],
        }
        for key, spec in PAGES.items()
    ]
    return {
        "university": UNIVERSITY,
        "pages": pages,
        "options": options(db),
    }


@app.get("/api/page/{page_id}")
def page(
    page_id: str, request: Request, db: Session = Depends(get_session)
) -> dict[str, Any]:
    spec = PAGES.get(page_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Unknown page")

    allowed = {f["name"] for f in spec["filters"]}
    supplied = {
        key: value
        for key, value in request.query_params.items()
        if key in allowed and value != ""
    }
    rows = spec["run"](db, **supplied)
    return {"rows": rows, "count": len(rows)}


@app.get("/api/record/{kind}/{key:path}")
def record(
    kind: str, key: str, db: Session = Depends(get_session)
) -> dict[str, Any]:
    loader = DETAILS.get(kind)
    if loader is None:
        raise HTTPException(status_code=404, detail="Unknown record type")
    result = loader(db, key)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found")
    return result


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "university": UNIVERSITY}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
