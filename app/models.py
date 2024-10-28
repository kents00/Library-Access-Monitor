from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    barangay = db.Column(db.String(100), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)

    # Relationship to students
    students = db.relationship('Student', back_populates='location')

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationship to students
    students = db.relationship('Student', back_populates='course')

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.String(10), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)

    # Reference to Location
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    location = db.relationship('Location', back_populates='students')

    # Reference to Course
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship('Course', back_populates='students')

    image = db.Column(db.String(200), nullable=True)
    is_logged_in = db.Column(db.Boolean, default=False)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), db.ForeignKey('student.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.now())

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
