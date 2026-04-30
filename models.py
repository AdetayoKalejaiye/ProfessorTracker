from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


def _gen_id():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String, primary_key=True, default=_gen_id)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tracked_professors = db.relationship(
        "TrackedProfessor", backref="user", cascade="all, delete-orphan"
    )


class Professor(db.Model):
    __tablename__ = "professor"

    id = db.Column(db.String, primary_key=True, default=_gen_id)
    name = db.Column(db.String, nullable=False)
    university = db.Column(db.String, nullable=False)
    department = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    interests = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    country = db.Column(db.String, default="USA")
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tracked = db.relationship("TrackedProfessor", backref="professor")


class TrackedProfessor(db.Model):
    __tablename__ = "tracked_professor"

    id = db.Column(db.String, primary_key=True, default=_gen_id)
    user_id = db.Column(
        db.String, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    professor_id = db.Column(
        db.String, db.ForeignKey("professor.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String, default="NOT_CONTACTED")
    notes = db.Column(db.String, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (db.UniqueConstraint("user_id", "professor_id"),)
