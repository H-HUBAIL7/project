# University Records

Record management system for Ashcombe University, built for the group
assignment. FastAPI backend,
SQLAlchemy models, and a browser interface for running the assignment
queries against the database.

## Run

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python -m app.seed
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000

`app.seed` creates the schema and loads dummy data. It defaults to
SQLite at `./university.db`. For another engine, set `DATABASE_URL`
before seeding and install the matching driver:

    export DATABASE_URL='postgresql+psycopg://user:pass@localhost/university'

## Layout

    app/database.py   engine and session
    app/models.py     ORM models
    app/records.py    search and record queries
    app/reports.py    report queries
    app/seed.py       schema creation and dummy data
    app/main.py       API and query registry
    app/static/       interface

## Queries

All eleven queries suggested in the project are implemented, plus search
and record views. Query functions live in `app/records.py` and
`app/reports.py`, each taking a session and returning a list of
dictionaries.

## Interface

Two sections. **Search** covers Students, Staff, Courses, Programmes,
Departments and Research as filterable lists, each row opening a record
page with tabs. **Reports** covers Achievement, Students, Courses,
Publications, Supervision and Workforce.

The institution name is the `UNIVERSITY` constant in `app/main.py`.
