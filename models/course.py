from . import db

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False, unique=True)

    # Changed from backref to back_populates to match Student model
    students = db.relationship('Student', back_populates='course')

    def to_dict(self):
        return {
            'id': self.id,
            'course_name': self.course_name
        }