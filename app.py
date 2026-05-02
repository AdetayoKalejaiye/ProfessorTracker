import json
import math
import os
import re
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
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
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
CROSSREF_BASE_URL = os.environ.get("CROSSREF_BASE_URL", "https://api.crossref.org")
ORCID_BASE_URL = os.environ.get("ORCID_BASE_URL", "https://pub.orcid.org/v3.0")
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


def tokenize_text(value):
    return [token for token in re.split(r"[^a-z0-9]+", normalize_text(value).lower()) if token]


def fetch_json(url, headers=None, timeout=12):
    request = Request(url, headers=headers or {"Accept": "application/json", "User-Agent": OPENALEX_USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


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


def professor_search_score(professor, query, department=""):
    query = normalize_text(query).lower()
    department = normalize_text(department).lower()
    name = professor.name.lower()
    university = professor.university.lower()
    dept = professor.department.lower()
    city = professor.city.lower()
    interests = professor.interests.lower()
    email = professor.email.lower()

    score = 1000

    if department:
        if dept == department:
            score -= 380
        elif department in dept:
            score -= 240
        elif department in interests:
            score -= 160
        elif department in university:
            score -= 90

    if query:
        if name == query:
            score -= 520
        elif name.startswith(query):
            score -= 360
        elif query in name:
            score -= 280

        if university == query:
            score -= 460
        elif university.startswith(query):
            score -= 300
        elif query in university:
            score -= 220

        if city == query:
            score -= 420
        elif city.startswith(query):
            score -= 260
        elif query in city:
            score -= 180

        if dept == query:
            score -= 430
        elif query in dept:
            score -= 260

        if query in email:
            score -= 120

        if query in interests:
            score -= 240

        query_tokens = tokenize_text(query)
        if query_tokens:
            interest_tokens = tokenize_text(interests)
            dept_tokens = tokenize_text(dept)
            university_tokens = tokenize_text(university)
            overlap = len(set(query_tokens) & set(interest_tokens))
            dept_overlap = len(set(query_tokens) & set(dept_tokens))
            university_overlap = len(set(query_tokens) & set(university_tokens))
            score -= overlap * 70
            score -= dept_overlap * 90
            score -= university_overlap * 35

    return (score, name)


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

    return fetch_json(url)


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


def openalex_query_authors(query=None, institution_ids=None, per_page=100):
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


def semantic_scholar_search_authors(query, per_page=100):
    try:
        params = {"query": query, "limit": per_page, "fields": "authorId,name,affiliations,hIndex"}
        url = f"https://api.semanticscholar.org/graph/v1/author/search?{urlencode(params)}"
        data = fetch_json(url)
        return data.get("data") or []
    except Exception:
        return []


def semantic_scholar_to_professor_fields(author):
    name = normalize_text(author.get("name")) or "Unknown"
    affiliations = author.get("affiliations") or []
    university = affiliations[0].get("name") if affiliations else "Unknown"
    author_id = author.get("authorId") or ""
    synthetic_email = f"{LIVE_EMAIL_PREFIX}ss-{author_id}@semanticscholar.local"
    return name, university, synthetic_email


def ror_search_institutions(query, per_page=50):
    try:
        params = {"query": query, "page": 1, "per_page": per_page}
        url = f"https://api.ror.org/organizations?{urlencode(params)}"
        data = fetch_json(url)
        return data.get("items") or []
    except Exception:
        return []


def ror_to_institution_fields(institution):
    name = normalize_text(institution.get("name")) or "Unknown"
    geo = institution.get("addresses", [{}])[0] if institution.get("addresses") else {}
    city = normalize_text(geo.get("city")) or normalize_text(name)
    country_code = normalize_text(geo.get("country_code")) or "US"
    latitude = geo.get("lat")
    longitude = geo.get("lng")
    return name, city, country_code, latitude, longitude


def crossref_search_works(query=None, affiliation_names=None, per_page=100):
    try:
        params = {"rows": per_page, "select": "author,affiliation,title,DOI"}
        if affiliation_names:
            quoted = [f'"{name}"' for name in affiliation_names if name]
            if quoted:
                params["query.affiliation"] = " OR ".join(quoted)
        if query and not affiliation_names:
            params["query.author"] = query

        url = f"{CROSSREF_BASE_URL.rstrip('/')}/works?{urlencode(params)}"
        data = fetch_json(url, headers={"Accept": "application/json", "User-Agent": OPENALEX_USER_AGENT})
        return (data.get("message") or {}).get("items") or []
    except Exception:
        return []


def crossref_to_author_candidates(items):
    candidates = []
    for item in items:
        title = normalize_text((item.get("title") or [""])[0])
        affiliations = item.get("affiliation") or []
        affiliation_name = normalize_text(affiliations[0].get("name")) if affiliations else ""
        authors = item.get("author") or []
        for author in authors:
            given = normalize_text(author.get("given"))
            family = normalize_text(author.get("family"))
            name = normalize_text(f"{given} {family}") or normalize_text(author.get("name"))
            if not name:
                continue
            synthetic_email = f"{LIVE_EMAIL_PREFIX}crossref-{name.lower().replace(' ', '-')[:64]}@crossref.local"
            candidates.append(
                {
                    "source": "crossref",
                    "author": {
                        "name": name,
                        "affiliation": affiliation_name,
                        "title": title,
                        "synthetic_email": synthetic_email,
                    },
                }
            )
    return candidates


def orcid_search_profiles(query=None, affiliation_names=None, per_page=100):
    try:
        params = {"rows": per_page}
        if affiliation_names:
            query_parts = [f'affiliation-org-name:"{name}"' for name in affiliation_names if name]
            if query_parts:
                params["q"] = " OR ".join(query_parts)
        elif query:
            params["q"] = query

        url = f"{ORCID_BASE_URL.rstrip('/')}/expanded-search/?{urlencode(params)}"
        data = fetch_json(url, headers={"Accept": "application/json", "User-Agent": OPENALEX_USER_AGENT})
        results = data.get("expanded-search") or data.get("expanded-search:expanded-result") or data.get("result") or []
        if isinstance(results, dict):
            results = [results]
        return results
    except Exception:
        return []


def orcid_to_author_candidates(results):
    candidates = []
    for result in results:
        if not isinstance(result, dict):
            continue
        orcid_id = normalize_text(result.get("orcid-id") or result.get("orcid") or result.get("orcid-id:orcid-id"))
        given = normalize_text(result.get("given-names") or result.get("given-name"))
        family = normalize_text(result.get("family-names") or result.get("family-name"))
        name = normalize_text(f"{given} {family}") or normalize_text(result.get("credit-name")) or normalize_text(result.get("given-and-family-names"))
        institution = normalize_text(result.get("institution-name") or result.get("current-institution-affiliation-name"))
        if not name:
            continue
        synthetic_email = f"{LIVE_EMAIL_PREFIX}orcid-{openalex_identifier(orcid_id) or name.lower().replace(' ', '-')[:64]}@orcid.local"
        candidates.append(
            {
                "source": "orcid",
                "author": {
                    "name": name,
                    "affiliation": institution,
                    "orcid_id": orcid_id,
                    "synthetic_email": synthetic_email,
                },
            }
        )
    return candidates


def multi_source_author_search(query, per_page=50):
    authors_by_name_inst = {}
    priority = 0

    try:
        openalex_authors = openalex_query_authors(query=query, per_page=per_page)
        for author in openalex_authors:
            name = normalize_text(author.get("display_name")) or ""
            inst = author.get("last_known_institutions", [{}])[0] if author.get("last_known_institutions") else {}
            inst_name = normalize_text(inst.get("display_name")) or ""
            key = (name.lower(), inst_name.lower())
            if key not in authors_by_name_inst:
                authors_by_name_inst[key] = {"source": "openalex", "author": author, "priority": priority}
            priority += 1
    except Exception:
        pass

    try:
        institution_names = []
        for inst in ror_search_institutions(query, per_page=25):
            name, *_ = ror_to_institution_fields(inst)
            if name:
                institution_names.append(name)

        crossref_items = crossref_search_works(query=query, affiliation_names=institution_names, per_page=per_page)
        for candidate in crossref_to_author_candidates(crossref_items):
            author = candidate["author"]
            name = normalize_text(author.get("name"))
            university = normalize_text(author.get("affiliation")) or "Unknown"
            key = (name.lower(), university.lower())
            if key not in authors_by_name_inst:
                authors_by_name_inst[key] = {"source": "crossref", "author": author, "priority": priority}
            priority += 1
    except Exception:
        pass

    try:
        institution_names = []
        for inst in ror_search_institutions(query, per_page=25):
            name, *_ = ror_to_institution_fields(inst)
            if name:
                institution_names.append(name)

        orcid_results = orcid_search_profiles(query=query, affiliation_names=institution_names, per_page=per_page)
        for candidate in orcid_to_author_candidates(orcid_results):
            author = candidate["author"]
            name = normalize_text(author.get("name"))
            university = normalize_text(author.get("affiliation")) or "Unknown"
            key = (name.lower(), university.lower())
            if key not in authors_by_name_inst:
                authors_by_name_inst[key] = {"source": "orcid", "author": author, "priority": priority}
            priority += 1
    except Exception:
        pass

    try:
        ss_authors = semantic_scholar_search_authors(query, per_page=per_page)
        for author in ss_authors:
            name, university, _ = semantic_scholar_to_professor_fields(author)
            key = (name.lower(), university.lower())
            if key not in authors_by_name_inst:
                authors_by_name_inst[key] = {"source": "semanticscholar", "author": author, "priority": priority}
            priority += 1
    except Exception:
        pass

    return sorted(authors_by_name_inst.values(), key=lambda x: x["priority"])


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
    professors.sort(key=lambda professor: professor_search_score(professor, query, department))
    return professors


def live_professors_for_search(query, department, range_miles):
    query = normalize_text(query)
    department = normalize_text(department)
    city_coords = resolve_city_coords(query)

    professors = []
    seen_people = set()

    try:
        institution_ids = []
        institution_names = []
        if query:
            institutions = openalex_find_institutions(query)
            institution_ids = [openalex_identifier(inst.get("id")) for inst in institutions if inst.get("id")]
            institution_names.extend([normalize_text(inst.get("display_name")) for inst in institutions if normalize_text(inst.get("display_name"))])

            for inst in ror_search_institutions(query, per_page=25):
                name, *_ = ror_to_institution_fields(inst)
                if name:
                    institution_names.append(name)
            institution_names = list(dict.fromkeys(institution_names))

        authors_with_source = []
        if city_coords and institution_ids:
            authors = openalex_query_authors(institution_ids=institution_ids, per_page=100)
            authors_with_source = [{"source": "openalex", "author": a} for a in authors]
        elif query and institution_ids:
            authors = openalex_query_authors(query=query, institution_ids=institution_ids, per_page=100)
            authors_with_source = [{"source": "openalex", "author": a} for a in authors]
        if query:
            authors_with_source.extend(multi_source_author_search(query, per_page=100))

            crossref_items = crossref_search_works(query=query, affiliation_names=institution_names, per_page=100)
            authors_with_source.extend(crossref_to_author_candidates(crossref_items))

            orcid_results = orcid_search_profiles(query=query, affiliation_names=institution_names, per_page=100)
            authors_with_source.extend(orcid_to_author_candidates(orcid_results))

        for item in authors_with_source:
            source = item.get("source", "openalex")
            author = item.get("author", {})
            
            if source == "semanticscholar":
                name, university, synthetic_email = semantic_scholar_to_professor_fields(author)
                dedupe_key = (normalize_text(name).lower(), normalize_text(university).lower())
                if dedupe_key in seen_people:
                    continue
                seen_people.add(dedupe_key)
                
                professor = Professor.query.filter_by(email=synthetic_email).first()
                if not professor:
                    professor = Professor(email=synthetic_email)
                    db.session.add(professor)
                
                professor.name = name
                professor.university = university
                professor.department = "Research"
                professor.interests = "Scholarly research"
                professor.city = "Unknown"
                professor.state = "US"
                professor.country = "USA"
                professor.latitude = 0.0
                professor.longitude = 0.0
            elif source in {"crossref", "orcid"}:
                name = normalize_text(author.get("name")) or "Unknown"
                university = normalize_text(author.get("affiliation")) or "Unknown"
                synthetic_email = author.get("synthetic_email") or f"{LIVE_EMAIL_PREFIX}{source}-{name.lower().replace(' ', '-')[:64]}@{source}.local"
                dedupe_key = (name.lower(), university.lower())
                if dedupe_key in seen_people:
                    continue
                seen_people.add(dedupe_key)

                professor = Professor.query.filter_by(email=synthetic_email).first()
                if not professor:
                    professor = Professor(email=synthetic_email)
                    db.session.add(professor)

                professor.name = name
                professor.university = university
                professor.department = "Research"
                professor.interests = normalize_text(author.get("title")) or "Scholarly research"
                professor.city = "Unknown"
                professor.state = "US"
                professor.country = "USA"
                professor.latitude = 0.0
                professor.longitude = 0.0
            else:
                professor = upsert_openalex_professor(author)
                dedupe_key = (normalize_text(professor.name).lower(), normalize_text(professor.university).lower())
                if dedupe_key in seen_people:
                    continue
                seen_people.add(dedupe_key)
            
            if not professor_matches_department(professor, department):
                continue

            if city_coords and professor.latitude != 0.0 and professor.longitude != 0.0:
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

    professors.sort(key=lambda professor: professor_search_score(professor, query, department))
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
    page = safe_int(request.args.get("page"), 1, minimum=1)
    per_page = safe_int(request.args.get("per_page"), 50, minimum=1, maximum=100)
    local_professors = local_professors_for_search(query, department)
    live_professors = live_professors_for_search(query, department, range_miles) if query else []

    combined = {}
    for professor in local_professors + live_professors:
        combined[professor.email] = professor

    if not query and not department:
        combined = {prof.email: prof for prof in local_professors}

    results = list(combined.values())
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = results[start:end]

    return jsonify(
        {
            "results": [serialize_professor(p) for p in paginated],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, math.ceil(total / per_page)) if total else 1,
            "has_more": end < total,
        }
    )


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
