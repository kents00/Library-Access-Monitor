from models import db

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.String(20), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    image = db.Column(db.String(255))
    managed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Modified relationships to avoid backref conflicts
    # Use back_populates instead of backref for clearer bidirectional relationships
    course = db.relationship('Course', back_populates='students')
    location = db.relationship('Location', back_populates='students')
    attendance_records = db.relationship('Attendance', back_populates='student', lazy=True)
    managed_by = db.relationship('User', foreign_keys=[managed_by_user_id], back_populates='managed_students')

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'age': self.age,
            'image': self.image,
            'course': {
                'id': self.course.id,
                'course_name': self.course.course_name
            } if self.course else None,
            'location': {
                'id': self.location.id,
                'barangay': self.location.barangay,
                'municipality': self.location.municipality,
                'province': self.location.province
            } if self.location else None,
            'managed_by': {
                'id': self.managed_by.id,
                'username': self.managed_by.username
            } if self.managed_by else None
        }