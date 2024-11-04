import os
import shutil
from app import app, db  # Import your Flask app and db instance
from models import Student

# Create an application context
with app.app_context():
    # Add a sample student
    student = Student(
    id = "2023304655",
    first_name = "Kent John",
    middle_name = "Mahinay",
    last_name = "Edoloverio",
    course = "Information Technology",
    age = 19,
    Barangay = "Colupan Bajo",
    Municipality = "Sinacaban",
    Province = "Misamis Occidental",
    image = "Kent.jpg",
    is_logged_in = False,
    )
    # Add to the session and commit
    db.session.add(student)
    db.session.commit()

    print('Sample student added successfully.')

# Define the path to the image and destination
IMAGE_SOURCE = 'Kent.jpg'  # Adjust this path
IMAGE_DESTINATION = 'static/uploads/Kent.jpg'

# Copy the image to the static/uploads directory
shutil.copy(IMAGE_SOURCE, IMAGE_DESTINATION)