from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Cancelled

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False) # emoji or class name
    order = db.Column(db.Integer, default=0)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    stars = db.Column(db.Integer, default=5)
    tag = db.Column(db.String(100))
    avatar_emoji = db.Column(db.String(10), default='👤')

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    image_path = db.Column(db.String(255), nullable=False)
    is_before_after = db.Column(db.Boolean, default=False)
    after_image_path = db.Column(db.String(255)) # Only used if is_before_after=True

class DoctorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    patients_count = db.Column(db.String(20), default='0')
    treatments_count = db.Column(db.String(20), default='0')
    profile_photo = db.Column(db.String(255))
