import datetime
from models import db
from flask import request, jsonify, current_app
from routes import student_bp
from models.student import Student
from models.attendance import Attendance

@student_bp.route('/', methods=['GET', 'POST'])
def login():
    student = None
    message = None
    success = True

    if request.method == 'POST':
        try:
            student_id = request.form['id']
            current_app.logger.info(f"Student ID entered: {student_id}")

            student = Student.query.filter_by(id=student_id).first()

            if student:
                # Check if student has already logged in today
                today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + datetime.timedelta(days=1)

                existing_attendance = Attendance.query.filter(
                    Attendance.student_id == student.id,
                    Attendance.check_in_time >= today_start,
                    Attendance.check_in_time < today_end
                ).first()

                if existing_attendance:
                    # Student already logged in today
                    success = False
                    login_time = existing_attendance.check_in_time.strftime('%I:%M %p')
                    message = f'You have already logged in today at {login_time}. Only one login per day is allowed.'
                    student_data = None
                    current_app.logger.info(f"Student {student_id} attempted duplicate login - already logged in at {login_time}")
                else:
                    # Create new attendance record for today
                    new_attendance = Attendance(
                        student_id=student.id,
                        check_in_time=datetime.datetime.now()
                    )
                    db.session.add(new_attendance)
                    db.session.commit()

                    student_data = student.to_dict()
                    if hasattr(student, 'course') and student.course and 'course' not in student_data:
                        student_data['course'] = {
                            'id': student.course.id,
                            'course_name': student.course.course_name
                        }

                    current_app.logger.info(f"Student {student_id} logged in successfully for the first time today")
            else:
                success = False
                message = 'No student ID number found. Please try again.'
                student_data = None
                current_app.logger.warning(f"Student ID {student_id} not found in database")

        except Exception as e:
            db.session.rollback()
            success = False
            message = f'An error occurred during login: {str(e)}'
            student_data = None
            current_app.logger.error(f"Error during student login: {str(e)}", exc_info=True)

    else:
        success = True
        message = None
        student_data = None

    return jsonify({
        'success': success,
        'message': message,
        'student': student_data
    })