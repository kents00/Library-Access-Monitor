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
            Location(id=1, barangay="East District", municipality="Central City", province="North Province"),
            Location(id=2, barangay="West District", municipality="Harbor Town", province="South Province"),
            Location(id=3, barangay="North District", municipality="Mountain View", province="East Province"),
            Location(id=4, barangay="South District", municipality="Valley City", province="West Province"),
            Location(id=5, barangay="Downtown", municipality="Metro City", province="Central Province"),
            Location(id=6, barangay="Uptown", municipality="Urban City", province="Coastal Province"),
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
                "id": "2023100001",
                "first_name": "John",
                "middle_name": "Michael",
                "last_name": "Doe",
                "age": 20,
                "location_id": 4,
                "course_id": 3,
                "image": "default_image.jpg",
                "is_logged_in": 1
            },
            {
                "id": "2023100002",
                "first_name": "Jane",
                "middle_name": "Alice",
                "last_name": "Smith",
                "age": 20,
                "location_id": 2,
                "course_id": 2,
                "image": "default_image.jpg",
                "is_logged_in": 1
            },
            {
                "id": "2023100003",
                "first_name": "Robert",
                "middle_name": "Thomas",
                "last_name": "Johnson",
                "age": 20,
                "location_id": 5,
                "course_id": 4,
                "image": "default_image.jpg",
                "is_logged_in": 1
            },
            {
                "id": "2023100004",
                "first_name": "Emily",
                "middle_name": "Grace",
                "last_name": "Brown",
                "age": 20,
                "location_id": 6,
                "course_id": 1,
                "image": "default_image.jpg",
                "is_logged_in": 1
            }
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
