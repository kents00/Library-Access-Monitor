import os
import shutil
from app import app, db  # Import your Flask app and db instance
from models import Student, Location, Course  # Import the necessary models

# Create an application context
with app.app_context():
    # Check if the Location exists; if not, create it
    location = Location.query.filter_by(
        barangay="Colupan Bajo",
        municipality="Sinacaban",
        province="Misamis Occidental"
    ).first()
    db.session.add(location)
    db.session.commit()  # Commit to generate an ID for the new location

    # Check if the Course exists; if not, create it
    course = Course.query.filter_by(course_name="Information Technology").first()
    db.session.add(course)
    db.session.commit()  # Commit to generate an ID for the new course

    # Add a sample student with references to Location and Course
    student = Student(
        id="2023304655",
        first_name="Kent John",
        middle_name="Mahinay",
        last_name="Edoloverio",
        course_id=course.id,  # Reference to Course
        location_id=location.id,  # Reference to Location
        age=19,
        image="Kent.jpg",
        is_logged_in=False
    )

    # Add to the session and commit
    db.session.add(student)
    db.session.commit()
    print('Sample student added successfully.')

# Define the path to the image and destination
IMAGE_SOURCE = 'Kent.jpg'  # Adjust this path as necessary
IMAGE_DESTINATION = 'static/uploads/Kent.jpg'

# Copy the image to the static/uploads directory
shutil.copy(IMAGE_SOURCE, IMAGE_DESTINATION)
