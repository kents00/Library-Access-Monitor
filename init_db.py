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
            # Create a default location for the admin user
            admin_location = Location(
                barangay="Admin District",
                municipality="Jimenez",
                province="Misamis Occidental"
            )
            db.session.add(admin_location)
            db.session.commit()  # Commit to get location ID

            admin = User(
                username='ustplibrary',
                email='admin@ustplibrary.edu.ph',
                first_name='Library',
                last_name='Administrator',
                phone='09123456789',
                password=generate_password_hash('ustplibrary@2025'),
                role='admin',
                location_id=admin_location.id,
                image='uploads/default_image.jpg'
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

# This allows the script to be run directly
if __name__ == '__main__':
    init_database()
