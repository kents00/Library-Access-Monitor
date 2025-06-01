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

    @classmethod
    def has_logged_in_today(cls, student_id):
        """Check if student has already logged in today"""
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + datetime.timedelta(days=1)

        return cls.query.filter(
            cls.student_id == student_id,
            cls.check_in_time >= today_start,
            cls.check_in_time < today_end
        ).first() is not None

    @classmethod
    def get_today_login(cls, student_id):
        """Get today's login record for a student"""
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + datetime.timedelta(days=1)

        return cls.query.filter(
            cls.student_id == student_id,
            cls.check_in_time >= today_start,
            cls.check_in_time < today_end
        ).first()

    @classmethod
    def get_unique_daily_logins(cls, start_date, end_date, course_id=None):
        """Get unique daily logins within date range"""
        from models.student import Student
        from models.course import Course

        query = db.session.query(
            cls.student_id,
            Student.first_name,
            Student.middle_name,
            Student.last_name,
            Course.course_name,
            db.func.date(cls.check_in_time).label('attendance_date'),
            db.func.min(cls.check_in_time).label('first_login_time')
        ).join(
            Student, Student.id == cls.student_id
        ).join(
            Course, Course.id == Student.course_id
        ).filter(
            cls.check_in_time >= start_date,
            cls.check_in_time <= end_date
        )

        if course_id:
            query = query.filter(Student.course_id == course_id)

        return query.group_by(
            cls.student_id,
            db.func.date(cls.check_in_time)
        ).all()
