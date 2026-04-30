import math
import os
from functools import wraps

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
    email = (data.get("email") or "").strip()
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
    email = (data.get("email") or "").strip()
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
    query = (request.args.get("q") or "").lower().strip()
    department = request.args.get("department") or ""
    range_miles = int(request.args.get("range") or 50)

    city_coords = CITY_COORDS.get(query) if query else None

    if city_coords:
        q = Professor.query
        if department:
            q = q.filter_by(department=department)
        professors = [
            p
            for p in q.all()
            if haversine(city_coords[0], city_coords[1], p.latitude, p.longitude)
            <= range_miles
        ]
    else:
        q = Professor.query
        if department:
            q = q.filter_by(department=department)
        if query:
            like = f"%{query}%"
            q = q.filter(
                db.or_(
                    Professor.university.ilike(like),
                    Professor.city.ilike(like),
                    Professor.name.ilike(like),
                )
            )
        professors = q.all()

    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "university": p.university,
                "department": p.department,
                "email": p.email,
                "interests": p.interests,
                "city": p.city,
                "state": p.state,
            }
            for p in professors
        ]
    )


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
                "professor": {
                    "id": t.professor.id,
                    "name": t.professor.name,
                    "university": t.professor.university,
                    "department": t.professor.department,
                    "email": t.professor.email,
                    "interests": t.professor.interests,
                    "city": t.professor.city,
                    "state": t.professor.state,
                },
            }
            for t in tracked
        ]
    )


@app.route("/api/tracked", methods=["POST"])
@login_required
def api_add_tracked():
    user_id = session["user_id"]
    data = request.get_json()
    professor_id = data.get("professorId")

    existing = TrackedProfessor.query.filter_by(
        user_id=user_id, professor_id=professor_id
    ).first()
    if existing:
        return jsonify(
            {"id": existing.id, "status": existing.status, "notes": existing.notes}
        )

    tracked = TrackedProfessor(user_id=user_id, professor_id=professor_id)
    db.session.add(tracked)
    db.session.commit()

    return jsonify(
        {"id": tracked.id, "status": tracked.status, "notes": tracked.notes}
    ), 201


@app.route("/api/tracked", methods=["PATCH"])
@login_required
def api_update_tracked():
    user_id = session["user_id"]
    data = request.get_json()
    tracked_id = data.get("id")

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
    data = request.get_json()
    tracked_id = data.get("id")

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
