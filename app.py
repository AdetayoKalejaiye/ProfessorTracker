import json
import math
import os
from functools import wraps
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import Professor, TrackedProfessor, User, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///app.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CITY_COORDS = {
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740),
    "philadelphia": (39.9526, -75.1652),
    "san antonio": (29.4241, -98.4936),
    "san diego": (32.7157, -117.1611),
    "dallas": (32.7767, -96.7970),
    "san francisco": (37.7749, -122.4194),
    "austin": (30.2672, -97.7431),
    "seattle": (47.6062, -122.3321),
    "denver": (39.7392, -104.9903),
    "boston": (42.3601, -71.0589),
    "atlanta": (33.7490, -84.3880),
    "miami": (25.7617, -80.1918),
    "minneapolis": (44.9778, -93.2650),
    "portland": (45.5051, -122.6750),
    "cambridge": (42.3736, -71.1097),
    "pasadena": (34.1478, -118.1445),
    "stanford": (37.4275, -122.1697),
    "berkeley": (37.8716, -122.2727),
    "princeton": (40.3573, -74.6672),
    "pittsburgh": (40.4406, -79.9959),
    "evanston": (42.0450, -87.6877),
    "ann arbor": (42.2808, -83.7430),
    "new haven": (41.3082, -72.9279),
}

OPENALEX_BASE_URL = os.environ.get("OPENALEX_BASE_URL", "https://api.openalex.org")
OPENALEX_CONTACT = os.environ.get("OPENALEX_CONTACT_EMAIL", "").strip()
OPENALEX_USER_AGENT = (
    f"ProfessorTracker/1.0 ({OPENALEX_CONTACT})"
    if OPENALEX_CONTACT
    else "ProfessorTracker/1.0"
)
LIVE_EMAIL_PREFIX = "openalex+"
DEFAULT_DEPARTMENTS = [
    "Computer Science",
    "Electrical Engineering",
    "Physics",
    "Mathematics",
    "Biology",
    "Chemistry",
    "Economics",
    "Psychology",
    "Neuroscience",
    "Data Science",
    "Statistics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Biomedical Engineering",
    "Linguistics",
    "Sociology",
]


def haversine(lat1, lon1, lat2, lon2):
    """Return distance in miles between two lat/lon points."""
    R = 3959
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalize_text(value):
    return " ".join(str(value or "").strip().split())


def safe_int(value, default, minimum=None, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def resolve_city_coords(query):
    query = normalize_text(query).lower()
    if not query:
        return None

    if query in CITY_COORDS:
        return CITY_COORDS[query]

    if "," in query:
        city = query.split(",", 1)[0].strip()
        if city in CITY_COORDS:
            return CITY_COORDS[city]

    return None


def serialize_professor(professor):
    return {
        "id": professor.id,
        "name": professor.name,
        "university": professor.university,
        "department": professor.department,
        "email": "" if professor.email.startswith(LIVE_EMAIL_PREFIX) else professor.email,
        "interests": professor.interests,
        "city": professor.city,
        "state": professor.state,
    }


def professor_search_score(professor, query):
    query = normalize_text(query).lower()
    if not query:
        return (0, professor.name.lower())

    fields = {
        "name": professor.name.lower(),
        "university": professor.university.lower(),
        "department": professor.department.lower(),
        "email": professor.email.lower(),
        "city": professor.city.lower(),
        "state": professor.state.lower(),
        "interests": professor.interests.lower(),
    }

    if fields["name"] == query:
        return (0, professor.name.lower())
    if fields["university"] == query:
        return (1, professor.name.lower())
    if fields["city"] == query:
        return (2, professor.name.lower())
    if fields["department"] == query:
        return (3, professor.name.lower())
    if fields["email"] == query:
        return (4, professor.name.lower())

    for index, field_name in enumerate(("name", "university", "city", "department", "email", "state", "interests"), start=5):
        if query in fields[field_name]:
            return (index, professor.name.lower())

    return (99, professor.name.lower())


def professor_matches_department(professor, department):
    department = normalize_text(department).lower()
    if not department:
        return True

    haystack = " ".join(
        [professor.department, professor.university, professor.city, professor.state, professor.interests]
    ).lower()
    return department in haystack


def professor_matches_query(professor, query):
    query = normalize_text(query).lower()
    if not query:
        return True

    haystack = " ".join(
        [professor.name, professor.university, professor.department, professor.email, professor.city, professor.state, professor.interests]
    ).lower()
    return query in haystack


def openalex_get(path, params=None):
    params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    url = f"{OPENALEX_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"

    request = Request(url, headers={"Accept": "application/json", "User-Agent": OPENALEX_USER_AGENT})
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def openalex_identifier(url_or_id):
    if not url_or_id:
        return ""
    return str(url_or_id).rstrip("/").rsplit("/", 1)[-1]


def synthetic_live_email(author_id):
    return f"{LIVE_EMAIL_PREFIX}{openalex_identifier(author_id)}@openalex.local"


def institution_geo_text(institution):
    geo = institution.get("geo") or {}
    city = normalize_text(geo.get("city"))
    region = normalize_text(geo.get("region"))
    country = normalize_text(geo.get("country") or geo.get("country_code"))
    return city, region, country, geo.get("latitude"), geo.get("longitude")


def openalex_find_institutions(query):
    data = openalex_get(
        "/institutions",
        {
            "search": query,
            "per_page": 10,
            "select": "id,display_name,geo,country_code,type",
        },
    )
    institutions = data.get("results") or []
    normalized = normalize_text(query).lower()
    return [
        inst
        for inst in institutions
        if normalized in normalize_text(inst.get("display_name")).lower()
        or normalized in normalize_text((inst.get("geo") or {}).get("city")).lower()
    ]


def openalex_query_authors(query=None, institution_ids=None, per_page=25):
    params = {
        "per_page": per_page,
        "select": "id,display_name,works_count,last_known_institutions,topics,affiliations",
    }

    if query:
        params["search"] = query
    if institution_ids:
        params["filter"] = f"last_known_institutions.id:{'|'.join(institution_ids)}"

    data = openalex_get("/authors", params)
    return data.get("results") or []


def openalex_author_department(author):
    topics = author.get("topics") or []
    if topics:
        return normalize_text(topics[0].get("display_name")) or "Research"
    return "Research"


def openalex_author_interests(author):
    topics = author.get("topics") or []
    interests = [normalize_text(topic.get("display_name")) for topic in topics if normalize_text(topic.get("display_name"))]
    return ", ".join(interests[:3]) or "Scholarly research"


def openalex_author_location(author):
    institutions = author.get("last_known_institutions") or []
    if not institutions:
        institutions = [((author.get("affiliations") or [{}])[0].get("institution") or {})]

    institution = institutions[0] if institutions else {}
    city, region, country, latitude, longitude = institution_geo_text(institution)

    if not city:
        city = normalize_text(institution.get("display_name")) or "Unknown"
    if not region:
        region = country or ""

    return city, region, country, latitude, longitude, institution.get("display_name") or ""


def upsert_openalex_professor(author):
    author_id = author.get("id") or ""
    synthetic_email = synthetic_live_email(author_id)
    professor = Professor.query.filter_by(email=synthetic_email).first()

    city, region, country, latitude, longitude, institution_name = openalex_author_location(author)
    if latitude is None or longitude is None:
        city_coords = resolve_city_coords(city)
        if city_coords:
            latitude, longitude = city_coords
        else:
            latitude = 0.0
            longitude = 0.0

    if not professor:
        professor = Professor(email=synthetic_email)
        db.session.add(professor)

    professor.name = normalize_text(author.get("display_name")) or "Unknown"
    professor.university = institution_name or "OpenAlex"
    professor.department = openalex_author_department(author)
    professor.interests = openalex_author_interests(author)
    professor.city = city
    professor.state = region
    professor.country = country or normalize_text((author.get("last_known_institutions") or [{}])[0].get("country_code")) or "USA"
    professor.latitude = float(latitude)
    professor.longitude = float(longitude)

    return professor


def local_professors_for_search(query, department):
    q = Professor.query
    if department:
        q = q.filter(Professor.department.ilike(f"%{department}%"))

    if query:
        like = f"%{query}%"
        q = q.filter(
            db.or_(
                Professor.university.ilike(like),
                Professor.city.ilike(like),
                Professor.state.ilike(like),
                Professor.department.ilike(like),
                Professor.name.ilike(like),
                Professor.email.ilike(like),
                Professor.interests.ilike(like),
            )
        )

    professors = q.all()
    professors.sort(key=lambda professor: professor_search_score(professor, query))
    return professors


def live_professors_for_search(query, department, range_miles):
    query = normalize_text(query)
    department = normalize_text(department)
    city_coords = resolve_city_coords(query)

    professors = []

    try:
        institution_ids = []
        if query:
            institutions = openalex_find_institutions(query)
            institution_ids = [openalex_identifier(inst.get("id")) for inst in institutions if inst.get("id")]

        authors = []
        if city_coords and institution_ids:
            authors = openalex_query_authors(institution_ids=institution_ids, per_page=25)
        elif query and institution_ids:
            authors = openalex_query_authors(query=query, institution_ids=institution_ids, per_page=25)
        elif query:
            authors = openalex_query_authors(query=query, per_page=25)

        for author in authors:
            professor = upsert_openalex_professor(author)
            if not professor_matches_department(professor, department):
                continue

            if city_coords:
                distance = haversine(
                    city_coords[0],
                    city_coords[1],
                    professor.latitude,
                    professor.longitude,
                )
                if distance > range_miles:
                    continue

            elif query and not professor_matches_query(professor, query):
                continue

            professors.append(professor)

        db.session.commit()
    except Exception:
        db.session.rollback()
        return []

    professors.sort(key=lambda professor: professor_search_score(professor, query))
    return professors


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("search"))
    return render_template("index.html")


@app.route("/search")
@login_required
def search():
    return render_template("search.html", user_email=session.get("user_email"))


@app.route("/list")
@login_required
def list_professors():
    return render_template("list.html", user_email=session.get("user_email"))


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------


@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = normalize_text(data.get("email")).lower()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    if not email or not name or not password:
        return jsonify({"error": "All fields required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    hashed = generate_password_hash(password)
    user = User(email=email, name=name, password=hashed)
    db.session.add(user)
    db.session.commit()

    return jsonify({"id": user.id, "email": user.email, "name": user.name}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = normalize_text(data.get("email")).lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    return jsonify({"id": user.id, "email": user.email, "name": user.name})


@app.route("/auth/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Professors API
# ---------------------------------------------------------------------------


@app.route("/api/professors/search")
@login_required
def api_search_professors():
    query = normalize_text(request.args.get("q"))
    department = normalize_text(request.args.get("department"))
    range_miles = safe_int(request.args.get("range"), 50, minimum=1, maximum=1000)
    local_professors = local_professors_for_search(query, department)
    live_professors = live_professors_for_search(query, department, range_miles) if query else []

    combined = {}
    for professor in local_professors + live_professors:
        combined[professor.email] = professor

    if not query and not department:
        combined = {prof.email: prof for prof in local_professors}

    return jsonify([serialize_professor(p) for p in combined.values()])


@app.route("/api/departments")
@login_required
def api_departments():
    departments = set(DEFAULT_DEPARTMENTS)
    departments.update(
        row[0]
        for row in db.session.query(Professor.department)
        .distinct()
        .order_by(Professor.department.asc())
        .all()
        if row[0]
    )
    return jsonify(sorted(departments))


@app.route("/api/professors", methods=["POST"])
@login_required
def api_create_professor():
    data = request.get_json(silent=True) or {}
    required_fields = ["name", "university", "department", "email", "interests", "city", "state"]

    missing = [field for field in required_fields if not normalize_text(data.get(field))]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    name = normalize_text(data.get("name"))
    university = normalize_text(data.get("university"))
    department = normalize_text(data.get("department"))
    email = normalize_text(data.get("email")).lower()
    interests = normalize_text(data.get("interests"))
    city = normalize_text(data.get("city"))
    state = normalize_text(data.get("state")).upper()

    if Professor.query.filter(db.func.lower(Professor.email) == email).first():
        return jsonify({"error": "A professor with that email already exists"}), 400

    coords = resolve_city_coords(city)
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if coords:
        latitude, longitude = coords
    else:
        latitude = safe_float(latitude)
        longitude = safe_float(longitude)

    if latitude is None or longitude is None:
        return jsonify(
            {
                "error": "Latitude and longitude are required when the city is not in the built-in location list"
            }
        ), 400

    professor = Professor(
        name=name,
        university=university,
        department=department,
        email=email,
        interests=interests,
        city=city,
        state=state,
        country=normalize_text(data.get("country")) or "USA",
        latitude=latitude,
        longitude=longitude,
    )
    db.session.add(professor)
    db.session.commit()

    return jsonify(serialize_professor(professor)), 201


# ---------------------------------------------------------------------------
# Tracked professors API
# ---------------------------------------------------------------------------


@app.route("/api/tracked", methods=["GET"])
@login_required
def api_get_tracked():
    user_id = session["user_id"]
    tracked = (
        TrackedProfessor.query.filter_by(user_id=user_id)
        .order_by(TrackedProfessor.created_at.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": t.id,
                "status": t.status,
                "notes": t.notes,
                "professorId": t.professor_id,
                "professor": serialize_professor(t.professor),
            }
            for t in tracked
        ]
    )


@app.route("/api/tracked", methods=["POST"])
@login_required
def api_add_tracked():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    professor_id = normalize_text(data.get("professorId"))

    if not professor_id:
        return jsonify({"error": "professorId is required"}), 400

    professor = Professor.query.filter_by(id=professor_id).first()
    if not professor:
        return jsonify({"error": "Professor not found"}), 404

    existing = TrackedProfessor.query.filter_by(
        user_id=user_id, professor_id=professor_id
    ).first()
    if existing:
        return jsonify({
            "id": existing.id,
            "status": existing.status,
            "notes": existing.notes,
            "professorId": existing.professor_id,
        })

    tracked = TrackedProfessor(user_id=user_id, professor_id=professor_id)
    db.session.add(tracked)
    db.session.commit()

    return jsonify(
        {
            "id": tracked.id,
            "status": tracked.status,
            "notes": tracked.notes,
            "professorId": tracked.professor_id,
        }
    ), 201


@app.route("/api/tracked", methods=["PATCH"])
@login_required
def api_update_tracked():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    tracked_id = normalize_text(data.get("id"))

    if not tracked_id:
        return jsonify({"error": "id is required"}), 400

    tracked = TrackedProfessor.query.filter_by(
        id=tracked_id, user_id=user_id
    ).first()
    if not tracked:
        return jsonify({"error": "Not found"}), 404

    if "status" in data:
        tracked.status = data["status"]
    if "notes" in data:
        tracked.notes = data["notes"]

    db.session.commit()
    return jsonify({"id": tracked.id, "status": tracked.status, "notes": tracked.notes})


@app.route("/api/tracked", methods=["DELETE"])
@login_required
def api_delete_tracked():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    tracked_id = normalize_text(data.get("id"))

    if not tracked_id:
        return jsonify({"error": "id is required"}), 400

    tracked = TrackedProfessor.query.filter_by(
        id=tracked_id, user_id=user_id
    ).first()
    if not tracked:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(tracked)
    db.session.commit()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
