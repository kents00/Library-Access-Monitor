from sqlalchemy import Column, Integer, String, Boolean
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    Barangay = db.Column(db.String(100), nullable=False)
    Municipality = db.Column(db.String(100), nullable=False)
    Province = db.Column(db.String(100), nullable=False)

    image = db.Column(db.String(200), nullable=True)  # Path to the image file
    is_logged_in = db.Column(db.Boolean, default=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), db.ForeignKey('student.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.now())


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)