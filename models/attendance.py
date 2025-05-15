from . import db
import datetime

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('students.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    # Changed from backref to back_populates to match Student model
    student = db.relationship('Student', back_populates='attendance_records')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'check_in_time': self.check_in_time
        }
