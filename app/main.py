from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_session
from .models import Course, Department, Enrollment, Grade, Lecturer, Staff, Student, course_lecturers

app = FastAPI(title="University Records API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/queries/students-by-course")
def students_by_course(course_code: str, lecturer_id: str, db: Session = Depends(get_session)):
    statement = (
        select(Student.student_id, Student.name)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .join(Course, Course.id == Enrollment.course_id)
        .join(course_lecturers, course_lecturers.c.course_id == Course.id)
        .join(Lecturer, Lecturer.id == course_lecturers.c.lecturer_id)
        .where(Course.code == course_code, Lecturer.lecturer_id == lecturer_id)
        .distinct()
    )
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/final-year-high-achievers")
def final_year_high_achievers(minimum_average: float = Query(70, ge=0, le=100), db: Session = Depends(get_session)):
    statement = (
        select(Student.student_id, Student.name, func.avg(Grade.score).label("average_grade"))
        .join(Grade, Grade.student_id == Student.id)
        .where(Student.year_of_study >= 4)
        .group_by(Student.id, Student.student_id, Student.name)
        .having(func.avg(Grade.score) > minimum_average)
    )
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/unregistered-students")
def unregistered_students(semester: str, academic_year: str, db: Session = Depends(get_session)):
    registered = select(Enrollment.student_id).where(Enrollment.semester == semester, Enrollment.academic_year == academic_year)
    statement = select(Student.student_id, Student.name).where(Student.id.not_in(registered))
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/student-advisor/{student_id}")
def student_advisor(student_id: str, db: Session = Depends(get_session)):
    statement = select(Student.name.label("student"), Lecturer.name.label("advisor"), Lecturer.email).join(Lecturer, Student.advisor_id == Lecturer.id).where(Student.student_id == student_id)
    result = db.execute(statement).mappings().first()
    if result is None:
        raise HTTPException(status_code=404, detail="Student or advisor not found")
    return dict(result)


@app.get("/queries/lecturers-by-expertise")
def lecturers_by_expertise(area: str, db: Session = Depends(get_session)):
    statement = select(Lecturer.lecturer_id, Lecturer.name, Lecturer.expertise).where(Lecturer.expertise.ilike(f"%{area}%"))
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/courses-by-department")
def courses_by_department(department: str, db: Session = Depends(get_session)):
    statement = select(Course.code, Course.name, Course.credits).join(Department).where(Department.name == department)
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/students-by-advisor/{lecturer_id}")
def students_by_advisor(lecturer_id: str, db: Session = Depends(get_session)):
    statement = select(Student.student_id, Student.name).join(Lecturer).where(Lecturer.lecturer_id == lecturer_id)
    return [dict(row) for row in db.execute(statement).mappings()]


@app.get("/queries/staff-by-department")
def staff_by_department(department: str, db: Session = Depends(get_session)):
    statement = select(Staff.staff_id, Staff.name, Staff.job_title).join(Department).where(Department.name == department)
    return [dict(row) for row in db.execute(statement).mappings()]
