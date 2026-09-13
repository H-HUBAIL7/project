# University Records API

A Python backend for the university record-management assignment. It provides a REST API and query endpoints, but deliberately does **not** create, include, or populate a database. Configure `DATABASE_URL` to point at an existing SQL database before running it.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://user:password@localhost/university'
uvicorn app.main:app --reload
```

The interactive API documentation is available at `/docs`.

## Assignment queries

The following query endpoints execute their SQL within the Python backend:

- `GET /queries/students-by-course`
- `GET /queries/final-year-high-achievers`
- `GET /queries/unregistered-students`
- `GET /queries/student-advisor/{student_id}`
- `GET /queries/lecturers-by-expertise`
- `GET /queries/courses-by-department`
- `GET /queries/students-by-advisor/{lecturer_id}`
- `GET /queries/staff-by-department`
