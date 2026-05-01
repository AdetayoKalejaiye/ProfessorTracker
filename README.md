# ProfessorTracker

A GitHub-styled web app for searching professors and tracking your outreach status.

## Features

- **Sign up / Sign in** – credential-based accounts
- **Search Faculty** – live search via OpenAlex by university name, city name, or professor name; filter by department
- **Faculty Cards** – shows name, university, topic/department, public email when available, city/state, and research interests
- **My List** – add professors to a personal tracking list
- **Email Status Tracking** – mark each as Not Contacted, Emailed, Answered, Rejected, or Pending
- **Inline Notes** – click to edit freeform notes per professor

## Tech Stack

- **Python** + **Flask**
- **SQLAlchemy** + **SQLite** for the database cache and tracking list
- **Werkzeug** for password hashing
- **Jinja2** for server-side HTML templates
- Vanilla JS + `fetch()` for dynamic interactions
- **OpenAlex** for live faculty/researcher data

## Getting Started

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file and set your secret
cp .env.example .env

# 4. Start the dev server
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

Optional: warm the local cache with live OpenAlex results:

```bash
python seed.py
```

## Data source

Faculty results are fetched live from OpenAlex and cached locally so they can be added to your list and tracked over time. The local database stores your account, tracked entries, and any cached live profiles.
