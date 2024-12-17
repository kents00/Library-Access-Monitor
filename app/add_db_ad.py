from werkzeug.security import generate_password_hash
from app import app, db  # Import your Flask app and db instance
from models import User

# Create an application context
with app.app_context():
    existing_admin = User.query.filter_by(username="kento").first()
    if not existing_admin:
        # Hash the password before storing
        hashed_password = generate_password_hash("12345")
        sample_admin = User(
            username="kento",
            password=hashed_password,  # Store the hashed password
            role="admin",
        )
        db.session.add(sample_admin)
        db.session.commit()
        print('Sample admin added successfully.')
    else:
        print('Admin already exists.')
