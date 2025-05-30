from . import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    image = db.Column(db.String(200), nullable=True)

    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    location = db.relationship('Location', back_populates='user')

    # Add relationships to allow user to edit students and courses
    managed_students = db.relationship('Student', foreign_keys='Student.managed_by_user_id', back_populates='managed_by')
    managed_courses = db.relationship('Course', foreign_keys='Course.managed_by_user_id', back_populates='managed_by')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'location_id': self.location_id,
            'password': self.password,
            'role': self.role,
            'image': self.image
        }