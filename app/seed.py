"""Create the schema and load dummy data. Run: python -m app.seed"""

from __future__ import annotations

import random
from datetime import date, timedelta

from .database import Base, SessionLocal, engine
from . import models as m

random.seed(2026)

FIRST = [
    "Amelia", "Noah", "Isla", "Oliver", "Freya", "Arthur", "Ivy", "Leo",
    "Maya", "Theo", "Nadia", "Rowan", "Priya", "Callum", "Zara", "Ethan",
    "Sofia", "Idris", "Hana", "Marcus", "Elena", "Tobias", "Ruth", "Omar",
    "Clara", "Felix", "Nour", "Duncan", "Anya", "Malik", "Bethan", "Kai",
    "Lena", "Rafael", "Sian", "Yusuf", "Erin", "Victor", "Mina", "Gareth",
    "Astrid", "Hugo", "Neve", "Samir", "Iona", "Bruno", "Talia", "Cormac",
    "Delphine", "Emre", "Greta", "Jonas", "Keziah", "Lorcan", "Marta",
    "Nikhil", "Orla", "Pascal", "Rhea", "Soren", "Tamsin", "Ulises",
    "Verity", "Wren", "Xanthe", "Yara", "Zeno", "Aoife", "Bram", "Cleo",
    "Dara", "Esme", "Finlay", "Giulia", "Halim", "Imogen", "Jasper",
    "Kirsten", "Linus", "Mabel", "Nils", "Ottilie", "Pablo", "Quinn",
    "Roisin", "Stellan", "Thea", "Ursula", "Vikram", "Willa", "Yannick",
]

LAST = [
    "Okafor", "Whitfield", "Nakamura", "Ellison", "Bradshaw", "Costa",
    "Radcliffe", "Haddad", "Lindqvist", "Milburn", "Devlin", "Osei",
    "Fairfax", "Kaur", "Novak", "Sandford", "Ferreira", "Ashworth",
    "Bergstrom", "Iqbal", "Hollins", "Moreau", "Petrov", "Quinn",
    "Salvatore", "Thorne", "Underwood", "Vance", "Wexler", "Yilmaz",
    "Abernathy", "Blackwood", "Castellan", "Dunmore", "Eastwick",
    "Fontaine", "Grimsby", "Harlowe", "Ingram", "Jarrow", "Kingsley",
    "Lambourne", "Marchetti", "Northcote", "Oakhurst", "Pemberton",
    "Quilling", "Ravensworth", "Strachan", "Tennyson", "Uxbridge",
    "Vasquez", "Whitmore", "Yelverton", "Zielinski", "Amara", "Beaumont",
    "Carrington", "Delacroix", "Esposito", "Fairweather", "Goodwin",
    "Hargreaves", "Ivanov", "Jankowski", "Kowalski", "Larsson", "Mbeki",
    "Nwosu", "Ohlsson", "Pankhurst", "Rasmussen", "Sinclair", "Tanaka",
    "Ueda", "Villeneuve", "Wainwright", "Xu", "Yusupov", "Zhao",
]

DEPARTMENTS = [
    ("Computer Science", "Faculty of Science and Engineering", "Ashfield"),
    ("Mathematics", "Faculty of Science and Engineering", "Ashfield"),
    ("Electronic Engineering", "Faculty of Science and Engineering",
     "Brownlow"),
    ("Physics", "Faculty of Science and Engineering", "Brownlow"),
    ("Business and Management", "Faculty of Social Sciences", "Sefton"),
    ("Economics", "Faculty of Social Sciences", "Sefton"),
    ("Biological Sciences", "Faculty of Health and Life Sciences",
     "Crown Street"),
    ("Psychology", "Faculty of Health and Life Sciences", "Crown Street"),
]

DEPT_AREAS = {
    "Computer Science": [
        "Machine Learning", "Distributed Systems", "Cryptography",
        "Human-Computer Interaction", "Software Verification",
    ],
    "Mathematics": [
        "Numerical Analysis", "Statistics", "Operational Research",
        "Topology",
    ],
    "Electronic Engineering": [
        "Signal Processing", "Embedded Systems", "Photonics",
    ],
    "Physics": [
        "Condensed Matter", "Astrophysics", "Quantum Optics",
    ],
    "Business and Management": [
        "Organisational Behaviour", "Finance", "Marketing Analytics",
    ],
    "Economics": [
        "Econometrics", "Development Economics", "Behavioural Economics",
    ],
    "Biological Sciences": [
        "Genomics", "Ecology", "Microbiology",
    ],
    "Psychology": [
        "Neuroscience", "Cognitive Psychology", "Clinical Psychology",
    ],
}

AREAS = sorted({a for pool in DEPT_AREAS.values() for a in pool})

PREFIX = {
    "Computer Science": "CS",
    "Mathematics": "MA",
    "Electronic Engineering": "EE",
    "Physics": "PH",
    "Business and Management": "BM",
    "Economics": "EC",
    "Biological Sciences": "BI",
    "Psychology": "PS",
}

TOPICS = {
    "Computer Science": [
        "Foundations of Programming", "Databases and Information Systems",
        "Algorithms and Complexity", "Software Engineering",
        "Machine Learning", "Distributed Systems", "Computer Networks",
        "Operating Systems", "Human-Computer Interaction",
    ],
    "Mathematics": [
        "Linear Algebra", "Calculus", "Probability and Statistics",
        "Numerical Methods", "Discrete Mathematics", "Real Analysis",
    ],
    "Electronic Engineering": [
        "Circuit Analysis", "Digital Logic", "Signals and Systems",
        "Embedded Programming", "Control Engineering",
        "Communication Systems",
    ],
    "Physics": [
        "Classical Mechanics", "Electromagnetism", "Quantum Mechanics",
        "Thermodynamics", "Astrophysics", "Computational Physics",
    ],
    "Business and Management": [
        "Principles of Management", "Corporate Finance",
        "Strategic Analysis", "Marketing", "Operations Management",
        "Business Analytics",
    ],
    "Economics": [
        "Microeconomics", "Macroeconomics", "Econometrics",
        "International Trade", "Public Economics", "Economic History",
    ],
    "Biological Sciences": [
        "Cell Biology", "Genetics", "Ecology and Evolution",
        "Microbiology", "Biochemistry", "Ecological Modelling",
    ],
    "Psychology": [
        "Introduction to Psychology", "Cognitive Psychology",
        "Developmental Psychology", "Research Methods",
        "Clinical Psychology", "Behavioural Neuroscience",
    ],
}

PROGRAMS = [
    ("BSc Computer Science", "BSc", 3, "Computer Science"),
    ("MSc Data Science", "MSc", 1, "Computer Science"),
    ("MSc Cyber Security", "MSc", 1, "Computer Science"),
    ("BSc Mathematics", "BSc", 3, "Mathematics"),
    ("MMath Mathematics", "MMath", 4, "Mathematics"),
    ("BEng Electronic Engineering", "BEng", 3, "Electronic Engineering"),
    ("MEng Electronic Engineering", "MEng", 4, "Electronic Engineering"),
    ("BSc Physics", "BSc", 3, "Physics"),
    ("MPhys Physics", "MPhys", 4, "Physics"),
    ("BA Business Management", "BA", 3, "Business and Management"),
    ("MSc Management", "MSc", 1, "Business and Management"),
    ("BSc Economics", "BSc", 3, "Economics"),
    ("MSc Economics", "MSc", 1, "Economics"),
    ("BSc Biological Sciences", "BSc", 3, "Biological Sciences"),
    ("MSc Genomics", "MSc", 1, "Biological Sciences"),
    ("BSc Psychology", "BSc", 3, "Psychology"),
]

ORGANISATIONS = [
    ("Computing Society", "Academic", 1998),
    ("Debating Union", "Academic", 1921),
    ("Mathematics Society", "Academic", 1956),
    ("Engineering Society", "Academic", 1934),
    ("Economics Forum", "Academic", 1978),
    ("Mountaineering Club", "Sport", 1954),
    ("Rowing Club", "Sport", 1889),
    ("Football Club", "Sport", 1902),
    ("Netball Club", "Sport", 1961),
    ("Chamber Orchestra", "Arts", 1967),
    ("Drama Society", "Arts", 1929),
    ("Photography Society", "Arts", 1984),
    ("Volunteering Network", "Community", 2004),
    ("Environmental Action", "Community", 2011),
    ("International Students Association", "Community", 1996),
    ("Entrepreneurship Hub", "Professional", 2015),
]

COMMITTEES = [
    ("Board of Studies", "Curriculum approval and academic standards."),
    ("Research Ethics Committee", "Review of research involving people."),
    ("Staff-Student Liaison", "Feedback channel between staff and students."),
    ("Health and Safety Committee", "Oversight of campus safety policy."),
    ("Equality and Diversity Panel", "Monitoring of inclusion commitments."),
    ("Library and Resources Group", "Allocation of learning resources."),
]

JOB_TITLES = [
    "Laboratory Technician", "Departmental Administrator", "IT Officer",
    "Student Support Adviser", "Facilities Coordinator", "Finance Officer",
    "Library Assistant", "Research Administrator", "Admissions Officer",
    "Technical Manager", "Communications Officer", "Timetabling Officer",
]

TITLES = ["Lecturer", "Senior Lecturer", "Reader", "Professor"]

STUDENT_JOBS = [
    "Student Ambassador", "Library Assistant", "Lab Demonstrator",
    "Open Day Guide", "Peer Mentor", "Society Coordinator",
]

FUNDERS = [
    "EPSRC", "BBSRC", "ESRC", "Wellcome Trust", "Horizon Europe",
    "Royal Society", "Innovate UK", "Leverhulme Trust",
    "Nuffield Foundation", "British Academy",
]

VENUES = [
    "Journal of Applied Computing", "Proceedings of ICDS",
    "Nature Communications", "European Journal of Management",
    "ACM Transactions on Systems", "Journal of Statistical Software",
    "IEEE Transactions on Signal Processing", "Physical Review Letters",
    "Journal of Economic Behaviour", "Molecular Biology Reports",
    "Cognitive Science Quarterly",
]

ANGLES = [
    "a case study", "an empirical review", "new methods",
    "a comparative analysis", "evidence from a cohort study",
    "a systematic evaluation", "theory and practice",
]

SECTORS = ["healthcare", "industry", "policy", "education", "agriculture"]

STREETS = [
    "Brownlow Hill", "Mount Pleasant", "Hope Street", "Falkner Square",
    "Rodney Street", "Canning Place",
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

SEMESTERS = [("Autumn", "2025/26"), ("Spring", "2025/26")]

N_LECTURERS = 90
N_STAFF = 70
N_STUDENTS = 800
N_PROJECTS = 60
N_PUBLICATIONS = 240


def make_names(count: int, used: set[str]) -> list[str]:
    names: list[str] = []
    while len(names) < count:
        candidate = f"{random.choice(FIRST)} {random.choice(LAST)}"
        if candidate in used:
            continue
        used.add(candidate)
        names.append(candidate)
    return names


def handle(name: str, seen: dict[str, int]) -> str:
    base = name.lower().replace(" ", ".")
    seen[base] = seen.get(base, 0) + 1
    return base if seen[base] == 1 else f"{base}{seen[base]}"


def build() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = SessionLocal()
    used: set[str] = set()
    seen: dict[str, int] = {}

    areas = {name: m.ResearchArea(name=name) for name in AREAS}
    session.add_all(areas.values())

    depts = {}
    for name, faculty, building in DEPARTMENTS:
        dept = m.Department(name=name, faculty=faculty, building=building)
        dept.research_areas = [areas[a] for a in DEPT_AREAS[name]]
        depts[name] = dept
    session.add_all(depts.values())
    session.flush()

    courses: dict[str, m.Course] = {}
    by_dept: dict[str, list[m.Course]] = {}
    for dept_name, topics in TOPICS.items():
        by_dept[dept_name] = []
        for index, topic in enumerate(topics):
            level = min(3, index // 3 + 1)
            code = f"{PREFIX[dept_name]}{level}{index % 3 + 1:02d}"
            course = m.Course(
                code=code,
                name=topic,
                description=f"{topic} at level {level}.",
                department=depts[dept_name],
                level=f"Level {level}",
                credits=random.choice([10, 15, 15, 20]),
                active=random.random() > 0.08,
            )
            courses[code] = course
            by_dept[dept_name].append(course)
    session.add_all(courses.values())
    session.flush()

    for group in by_dept.values():
        for course in group:
            level = int(course.level.split()[-1])
            earlier = [c for c in group if int(c.level.split()[-1]) < level]
            if earlier:
                course.prerequisites = random.sample(
                    earlier, min(len(earlier), random.randint(1, 2))
                )

    for course in courses.values():
        for _ in range(random.randint(1, 2)):
            start = random.choice([9, 11, 13, 15, 16])
            session.add(
                m.CourseSchedule(
                    course=course,
                    day_of_week=random.choice(DAYS),
                    start_time=f"{start:02d}:00",
                    end_time=f"{start + 2:02d}:00",
                    room=f"{random.choice('ABCDE')}{random.randint(1, 60)}",
                )
            )
        for title, kind in [
            (f"{course.name}: core text", "Textbook"),
            ("Lecture slides", "Slides"),
            ("Problem sheets", "Exercises"),
            ("Reading list", "Reading"),
        ]:
            session.add(
                m.CourseMaterial(
                    course=course,
                    title=title,
                    material_type=kind,
                    reference=f"{course.code}-{kind[:3].upper()}",
                    required=kind == "Textbook",
                )
            )

    programs = {}
    for name, degree, years, dept_name in PROGRAMS:
        programs[name] = m.Program(
            name=name,
            degree_awarded=degree,
            duration_years=years,
            department=depts[dept_name],
        )
    session.add_all(programs.values())
    session.flush()

    for name, _, years, dept_name in PROGRAMS:
        for course in by_dept[dept_name]:
            level = int(course.level.split()[-1])
            session.add(
                m.ProgramRequirement(
                    program=programs[name],
                    course=course,
                    year_of_study=min(level, years),
                    mandatory=level == 1,
                )
            )

    lecturers: list[m.Lecturer] = []
    for index, name in enumerate(make_names(N_LECTURERS, used)):
        dept_name = DEPARTMENTS[index % len(DEPARTMENTS)][0]
        lecturer = m.Lecturer(
            lecturer_id=f"L{index + 1:04d}",
            name=name,
            department=depts[dept_name],
            email=f"{handle(name, seen)}@ashcombe.ac.uk",
            phone=f"0151 794 {random.randint(1000, 9999)}",
            office=f"{random.choice('ABCDE')}.{random.randint(1, 120)}",
            academic_title=random.choices(
                TITLES, weights=[40, 30, 15, 15]
            )[0],
            appointed_on=date(2005, 1, 1)
            + timedelta(days=random.randint(0, 7000)),
            active=random.random() > 0.06,
        )
        pool = DEPT_AREAS[dept_name]
        lecturer.expertise = [
            areas[a] for a in random.sample(pool, min(2, len(pool)))
        ]
        lecturer.research_interests = [
            areas[a] for a in random.sample(AREAS, random.randint(1, 3))
        ]
        for award in random.sample(["PhD", "MSc", "MA", "BSc"], 2):
            session.add(
                m.Qualification(
                    lecturer=lecturer,
                    award=award,
                    subject=dept_name,
                    institution=random.choice(
                        ["Liverpool", "Manchester", "Leeds", "Bristol",
                         "Edinburgh", "Cardiff", "Durham", "Warwick"]
                    ),
                    year_awarded=random.randint(1996, 2018),
                )
            )
        lecturers.append(lecturer)
    session.add_all(lecturers)
    session.flush()

    by_dept_lect: dict[int, list[m.Lecturer]] = {}
    for lecturer in lecturers:
        by_dept_lect.setdefault(lecturer.department_id, []).append(lecturer)

    for course in courses.values():
        pool = by_dept_lect.get(course.department_id, lecturers)
        course.lecturers = random.sample(pool, min(len(pool), 2))

    for dept_name, pool in DEPT_AREAS.items():
        dept = depts[dept_name]
        candidates = by_dept_lect.get(dept.id, lecturers)
        heads = random.sample(candidates, min(len(candidates), 2))
        for position, area in enumerate(pool[:2]):
            session.add(
                m.ResearchGroup(
                    name=f"{area} Group",
                    department=dept,
                    head=heads[position] if position < len(heads) else None,
                )
            )

    committees = [m.Committee(name=n, remit=r) for n, r in COMMITTEES]
    session.add_all(committees)
    session.flush()

    for committee in committees:
        for position, lecturer in enumerate(random.sample(lecturers, 8)):
            session.add(
                m.CommitteeMembership(
                    committee=committee,
                    lecturer=lecturer,
                    role=(
                        "Chair" if position == 0
                        else "Secretary" if position == 1
                        else "Member"
                    ),
                )
            )

    orgs = [
        m.StudentOrganisation(name=n, category=c, founded_year=y)
        for n, c, y in ORGANISATIONS
    ]
    session.add_all(orgs)

    staff: list[m.Staff] = []
    for index, name in enumerate(make_names(N_STAFF, used)):
        dept_name = DEPARTMENTS[index % len(DEPARTMENTS)][0]
        start = date(2014, 1, 1) + timedelta(days=random.randint(0, 4000))
        fixed = index % 4 == 0
        staff.append(
            m.Staff(
                staff_id=f"N{index + 1:04d}",
                name=name,
                job_title=random.choice(JOB_TITLES),
                department=depts[dept_name],
                employment_type=random.choices(
                    ["Full-time", "Part-time", "Fixed-term"],
                    weights=[60, 25, 15],
                )[0],
                contract_start=start,
                contract_end=start + timedelta(days=1460) if fixed else None,
                salary_amount=round(random.uniform(25000, 56000), 2),
                emergency_contact_name=(
                    f"{random.choice(FIRST)} {random.choice(LAST)}"
                ),
                emergency_contact_phone=(
                    f"07{random.randint(10 ** 8, 10 ** 9 - 1)}"
                ),
                emergency_contact_relation=random.choice(
                    ["Spouse", "Parent", "Sibling", "Partner", "Friend"]
                ),
                active=random.random() > 0.07,
            )
        )
    session.add_all(staff)
    session.flush()

    students: list[m.Student] = []
    program_list = list(programs.values())
    for index, name in enumerate(make_names(N_STUDENTS, used)):
        program = random.choice(program_list)
        pool = by_dept_lect.get(program.department_id, lecturers)
        students.append(
            m.Student(
                student_id=f"S{index + 1:05d}",
                name=name,
                date_of_birth=date(1998, 1, 1)
                + timedelta(days=random.randint(0, 3200)),
                email=f"{handle(name, seen)}@student.ashcombe.ac.uk",
                phone=f"07{random.randint(10 ** 8, 10 ** 9 - 1)}",
                address=(
                    f"{random.randint(1, 240)} "
                    f"{random.choice(STREETS)}, Liverpool"
                ),
                program=program,
                year_of_study=random.randint(1, program.duration_years),
                graduation_status=random.choices(
                    ["active", "graduated", "withdrawn", "suspended"],
                    weights=[78, 14, 5, 3],
                )[0],
                advisor=random.choice(pool),
            )
        )
    session.add_all(students)
    session.flush()

    for student in students:
        for org in random.sample(orgs, random.randint(0, 3)):
            session.add(
                m.OrganisationMembership(
                    student=student,
                    organisation=org,
                    role=random.choices(
                        [None, "Member", "Treasurer", "President",
                         "Secretary"],
                        weights=[35, 45, 8, 6, 6],
                    )[0],
                    joined_on=date(2024, 9, random.randint(1, 28)),
                )
            )

    requirements: dict[int, list[m.ProgramRequirement]] = {}
    for requirement in session.query(m.ProgramRequirement).all():
        requirements.setdefault(requirement.program_id, []).append(requirement)

    for student in students:
        if random.random() < 0.06:
            continue
        options = [
            r.course for r in requirements.get(student.program_id, [])
            if r.year_of_study <= student.year_of_study and r.course.active
        ]
        if not options:
            continue
        chosen = random.sample(
            options, min(len(options), random.randint(4, 7))
        )
        ability = random.gauss(0, 9)
        for course in chosen:
            for semester, year in SEMESTERS:
                if random.random() < 0.6:
                    session.add(
                        m.Enrollment(
                            student=student,
                            course=course,
                            semester=semester,
                            academic_year=year,
                        )
                    )
            session.add(
                m.Grade(
                    student=student,
                    course=course,
                    score=max(0, min(100, round(
                        random.gauss(62, 12) + ability, 1
                    ))),
                    semester=SEMESTERS[0][0],
                    academic_year=SEMESTERS[0][1],
                )
            )

    reasons = [
        "Late submission without extenuating circumstances.",
        "Unauthorised materials in an examination.",
        "Breach of laboratory safety procedure.",
        "Plagiarism identified by similarity report.",
        "Disruption during a scheduled lecture.",
        "Misuse of library resources.",
    ]
    for student in random.sample(students, 70):
        for _ in range(random.randint(1, 2)):
            session.add(
                m.DisciplinaryRecord(
                    student=student,
                    incident_date=date(
                        2025, random.randint(1, 12), random.randint(1, 28)
                    ),
                    details=random.choice(reasons),
                    outcome=random.choice(
                        ["Formal warning", "Mark capped",
                         "No further action", "Referred to panel",
                         "Written apology required"]
                    ),
                )
            )

    for student in random.sample(students, 130):
        session.add(
            m.StudentEmployment(
                student=student,
                supervisor=random.choice(staff),
                job_title=random.choice(STUDENT_JOBS),
                hours_per_week=round(random.uniform(4, 16), 1),
                start_date=date(2025, 9, random.randint(1, 28)),
            )
        )

    projects: list[m.ResearchProject] = []
    for index in range(N_PROJECTS):
        start = date(2021, 1, 1) + timedelta(days=random.randint(0, 1500))
        projects.append(
            m.ResearchProject(
                title=(
                    f"{random.choice(AREAS)} for "
                    f"{random.choice(SECTORS)} ({index + 1:03d})"
                ),
                principal_investigator=random.choice(lecturers),
                start_date=start,
                end_date=start + timedelta(days=random.randint(500, 1600)),
                status=random.choices(
                    ["active", "completed", "proposed"],
                    weights=[55, 35, 10],
                )[0],
                outcomes=random.choice(
                    [
                        "Open-source toolkit released.",
                        "Policy briefing delivered to the funder.",
                        "Two doctoral studentships completed.",
                        "Industrial partnership established.",
                        "Dataset published under open licence.",
                    ]
                ),
            )
        )
    session.add_all(projects)
    session.flush()

    for project in projects:
        for funder in random.sample(FUNDERS, random.randint(1, 3)):
            session.add(
                m.ProjectFunding(
                    project=project,
                    funder=funder,
                    grant_reference=(
                        f"{funder[:3].upper()}/"
                        f"{random.randint(100000, 999999)}"
                    ),
                    amount=round(random.uniform(35000, 1250000), 2),
                )
            )
        for lecturer in random.sample(lecturers, random.randint(1, 5)):
            session.add(
                m.ProjectMember(
                    project=project,
                    lecturer=lecturer,
                    role=random.choice(
                        ["Co-investigator", "Researcher", "Collaborator"]
                    ),
                )
            )
        for student in random.sample(students, random.randint(0, 5)):
            session.add(
                m.ProjectMember(
                    project=project,
                    student=student,
                    role=random.choice(
                        ["Research assistant", "Doctoral researcher"]
                    ),
                )
            )

    for _ in range(N_PUBLICATIONS):
        publication = m.Publication(
            title=f"{random.choice(AREAS)}: {random.choice(ANGLES)}",
            venue=random.choice(VENUES),
            publication_type=random.choices(
                ["Journal article", "Conference paper", "Book chapter",
                 "Preprint"],
                weights=[45, 35, 12, 8],
            )[0],
            published_on=date.today()
            - timedelta(days=random.randint(5, 1500)),
            doi=f"10.1000/ash.{random.randint(10000, 99999)}",
            project_id=random.choice(projects).id,
        )
        publication.authors = random.sample(lecturers, random.randint(1, 4))
        session.add(publication)

    session.commit()

    counts = {
        "departments": len(depts),
        "programmes": len(programs),
        "courses": len(courses),
        "lecturers": len(lecturers),
        "staff": len(staff),
        "students": len(students),
        "projects": len(projects),
        "publications": N_PUBLICATIONS,
    }
    session.close()
    print("database built:")
    for key, value in counts.items():
        print(f"  {key:14} {value}")


if __name__ == "__main__":
    build()
