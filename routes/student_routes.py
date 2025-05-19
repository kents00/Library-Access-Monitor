import datetime
from models import db
from flask import request, jsonify
from routes import student_bp
from models.student import Student
from models.attendance import Attendance

@student_bp.route('/', methods=['GET', 'POST'])
def login():
    student = None
    message = None
    success = True

    if request.method == 'POST':
        student_id = request.form['id']
        print(f"Student ID entered: {student_id}")

        student = Student.query.filter_by(id=student_id).first()

        if student:
            # Create attendance record without modifying is_logged_in
            new_attendance = Attendance(
                student_id=student.id, check_in_time=datetime.datetime.now())
            db.session.add(new_attendance)
            db.session.commit()
            student_data = student.to_dict()
            if hasattr(student, 'course') and student.course and 'course' not in student_data:
                student_data['course'] = {
                    'id': student.course.id,
                    'course_name': student.course.course_name
                }
        else:
            success = False
            message = 'No student ID number found. Please try again.'
            student_data = None

    else:
        success = True
        message = None
        student_data = None

    return jsonify({
        'success': success,
        'message': message,
        'student': student_data
    })