import os
import shutil
from app import app, db  # Import your Flask app and db instance
from models import Student

# Define the path to the image and destination
IMAGE_SOURCE = 'sample.png'  # Adjust this path
IMAGE_DESTINATION = 'static/uploads/sample.png'

# Copy the image to the static/uploads directory
shutil.copy(IMAGE_SOURCE, IMAGE_DESTINATION)

# Create an application context
with app.app_context():
    # Add a sample student
    sample_student = Student(
        id="12345",  # Unique ID
        first_name="KENT JOHN",
        middle_name="MAHINAY",
        last_name="EDOLOVERIO",
        course="Information Technology",
        age=19,
        place_of_residence="Sinacaban",
        image="sample.png"  # Store the filename only
    )

    # Add to the session and commit
    db.session.add(sample_student)
    db.session.commit()

    print('Sample student added successfully.')
