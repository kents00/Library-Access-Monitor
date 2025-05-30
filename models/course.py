from . import db

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False, unique=True)
    managed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    students = db.relationship('Student', back_populates='course')
    managed_by = db.relationship('User', foreign_keys=[managed_by_user_id], back_populates='managed_courses')

    def to_dict(self):
        return {
            'id': self.id,
            'course_name': self.course_name,
            'managed_by': {
                'id': self.managed_by.id,
                'username': self.managed_by.username
            } if self.managed_by else None
        }