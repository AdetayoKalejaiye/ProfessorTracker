# ProfessorTracker

A GitHub-styled web app for searching professors and tracking your outreach status.

## Features

- **Sign up / Sign in** – credential-based accounts
- **Search Professors** – search by university name, city name (with distance range), or professor name; filter by department
- **Professor Cards** – shows name, university, department, email, city/state, and research interests
- **My List** – add professors to a personal tracking list
- **Email Status Tracking** – mark each as Not Contacted, Emailed, Answered, Rejected, or Pending
- **Inline Notes** – click to edit freeform notes per professor

## Tech Stack

- **Python** + **Flask**
- **SQLAlchemy** + **SQLite** for the database
- **Werkzeug** for password hashing
- **Jinja2** for server-side HTML templates
- Vanilla JS + `fetch()` for dynamic interactions

## Getting Started

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file and set your secret
cp .env.example .env

# 4. Seed the database with professors
python seed.py

# 5. Start the dev server
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

## Database

The seed script populates ~51 professors across 15 universities (MIT, Stanford, Harvard, Carnegie Mellon, UC Berkeley, Caltech, Princeton, Yale, Columbia, University of Michigan, Georgia Tech, UT Austin, UCLA, NYU, Northwestern) in departments including Computer Science, Electrical Engineering, Physics, Mathematics, Biology, Chemistry, Economics, Psychology, Neuroscience, and Data Science.
