from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


def _gen_id():
    return str(uuid.uuid4())


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
