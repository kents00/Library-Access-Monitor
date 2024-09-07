from app import app, db  # Import your Flask app and db instance
from models import Student

# Create an application context
with app.app_context():
    # Add a sample student
    sample_student = Student(
        id='123456',  # Sample ID
        name='Kent',
        course='Information Technology',
        age=20,
        place_of_residence='Downtown'
    )

    # Add to the session and commit
    db.session.add(sample_student)
    db.session.commit()

    print('Sample student added successfully.')
