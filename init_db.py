from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from models import db
from models.user import User
from models.course import Course
from models.location import Location
from models.student import Student
from config import Config
import os

def init_database(app=None):
    """Initialize the database with default data."""
    # If no app was provided, create a temporary one for initialization
    if app is None:
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)

    with app.app_context():
        # Clean up existing database if needed
        db.drop_all()  # This will remove any existing tables that have inconsistent definitions
        db.create_all()  # Recreate all tables with proper relationships

        # Create default admin user if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                role='admin'
            )
            db.session.add(admin)

        # Create basic courses
        if Course.query.count() == 0:
            courses = [
                Course(course_name='Information Technology'),
                Course(course_name='Marine Biology'),
                Course(course_name='Home Economics and Industrial Arts'),
                Course(course_name='Technology and Livelihood Education'),
            ]
            db.session.add_all(courses)
            db.session.commit()  # Commit to generate course IDs

        # Create locations for student records with better dummy names
        locations = [
            Location(id=1, barangay="East District", municipality="Jimenez", province="Misamis Occidental"),
            Location(id=2, barangay="Punta", municipality="Panaon", province="Misamis Occidental"),
            Location(id=3, barangay="Butuay", municipality="Jimenez", province="Misamis Occidental"),
            Location(id=4, barangay="Colupan Bajo", municipality="Sinacaban", province="Misamis Occidental"),
            Location(id=5, barangay="Lupez", municipality="Culo Molave", province="Zamboanga del Sur"),
        ]
        for location in locations:
            # Check if location already exists
            existing_location = Location.query.filter_by(id=location.id).first()
            if not existing_location:
                db.session.add(location)

        db.session.commit()  # Commit to generate location IDs

        # Add student data with dummy information
        students_data = [
            {
                "id": "2023301341",
                "first_name": "Euri",
                "middle_name": "Acope",
                "last_name": "Buladaco",
                "age": 20,
                "location_id": 1,
                "course_id": 3,
                "image": "Euri.jpg",
            },
            {
                "id": "2023301346",
                "first_name": "Liedyl",
                "middle_name": "Albino",
                "last_name": "Castillo",
                "age": 20,
                "location_id": 2,
                "course_id": 2,
                "image": "Liedyl.jpg",
            },
            {
                "id": "2023301393",
                "first_name": "Ma.Daisy Mae",
                "middle_name": "Luzon",
                "last_name": "Redera",
                "age": 20,
                "location_id": 3,
                "course_id": 4,
                "image": "Redera.jpg",
            },
            {
                "id": "2023304655",
                "first_name": "Kent John",
                "middle_name": "Mahinay",
                "last_name": "Edoloverio",
                "age": 20,
                "location_id": 4,
                "course_id": 1,
                "image": "Kent.jpg",
            },
            {
                "id": "2023304607",
                "first_name": "Cristian Mark",
                "middle_name": "Roble",
                "last_name": "Catiloc",
                "age": 20,
                "location_id": 5,
                "course_id": 1,
                "image": "Cristian.jpg",
            },
        ]

        # Add students
        for student_data in students_data:
            # Check if student already exists
            existing_student = Student.query.filter_by(id=student_data["id"]).first()
            if not existing_student:
                student = Student(
                    id=student_data["id"],
                    first_name=student_data["first_name"],
                    middle_name=student_data["middle_name"],
                    last_name=student_data["last_name"],
                    age=student_data["age"],
                    location_id=student_data["location_id"],
                    course_id=student_data["course_id"],
                    image=student_data["image"]
                )
                db.session.add(student)

        db.session.commit()
        print("Database initialized successfully with default users!")

        # Ensure the uploads directory exists
        uploads_dir = os.path.join(app.static_folder, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            print(f"Created uploads directory at {uploads_dir}")

# This allows the script to be run directly
if __name__ == '__main__':
    init_database()
