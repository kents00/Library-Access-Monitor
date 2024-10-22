from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Student, Attendance, User
from datetime import datetime, timedelta
from flask import Response, make_response, render_template
from sqlalchemy import extract
from weasyprint import HTML
import os
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'

db.init_app(app)

with app.app_context():
    db.create_all()

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def export_attendance_csv(start_date):
    attendance_data = db.session.query(Attendance, Student).join(Student).filter(Attendance.check_in_time >= start_date).all()

    def generate():
        yield b"ID,First Name,Last Name,Course,Check-in Time\n"
        for attendance, student in attendance_data:
            yield f"{student.id},{student.first_name},{student.last_name},{student.course},{attendance.check_in_time}\n".encode('utf-8')

    return Response(generate(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=attendance_data.csv"})

@app.route('/', methods=['GET', 'POST'])
def login():
    student = None

    if request.method == 'POST':
        student_id = request.form['id']
        print(f"Student ID entered: {student_id}")

        student = Student.query.filter_by(id=student_id).first()

        if student:
            new_attendance = Attendance(student_id=student.id, check_in_time=datetime.now())
            db.session.add(new_attendance)
            student.is_logged_in = True
            db.session.commit()
        else:
            flash('Invalid ID. Please try again.')

    return render_template('login.html', student=student)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' in session:
        filter_type = request.form.get('filter') if request.method == 'POST' else 'weekly'
        today = datetime.now()

        if filter_type == 'weekly':
            start_date = today - timedelta(weeks=1)
        elif filter_type == 'monthly':
            start_date = today - timedelta(weeks=4)
        elif filter_type == 'yearly':
            start_date = today - timedelta(weeks=52)

        if request.method == 'POST' and 'export_csv' in request.form:
            return export_attendance_csv(start_date)

        attendance_data = db.session.query(Attendance, Student).join(Student, Attendance.student_id == Student.id).filter(Attendance.check_in_time >= start_date).all()

        course_visits_raw = db.session.query(Student.course, db.func.count(Attendance.id).label('visits')).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.course).all()

        course_visits = [{"course": course, "visits": visits} for course, visits in course_visits_raw]

        age_groups = {
            'Under 18': 0,
            '18-25': 0,
            '26-35': 0,
            '36-50': 0,
            'Above 50': 0
        }
        for attendance, student in attendance_data:
            if student.age < 18:
                age_groups['Under 18'] += 1
            elif 18 <= student.age <= 25:
                age_groups['18-25'] += 1
            elif 26 <= student.age <= 35:
                age_groups['26-35'] += 1
            elif 36 <= student.age <= 50:
                age_groups['36-50'] += 1
            else:
                age_groups['Above 50'] += 1

        place_visits_raw = db.session.query(Student.Municipality, db.func.count(Attendance.id).label('visits')).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.Municipality).all()

        place_visits = [{"municipality": place, "visits": visits} for place, visits in place_visits_raw]

        logged_in_users = db.session.query(Student, db.func.max(Attendance.check_in_time).label('login_time')).join(Attendance, Student.id == Attendance.student_id).filter(Student.is_logged_in == True).group_by(Student.id).all()

        total_visitors = db.session.query(Attendance.student_id).filter(Attendance.check_in_time >= start_date).distinct().count()

        course_visits_by_month = db.session.query(
            Student.course,
            extract('month', Attendance.check_in_time).label('month'),
            db.func.count(Attendance.id).label('visits')
        ).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.course, 'month').all()

        monthly_course_visits = {
            'Information Technology': [0] * 12,
            'Marine Biology': [0] * 12,
            'Education': [0] * 12
        }

        for course, month, visits in course_visits_by_month:
            if course in monthly_course_visits:
                monthly_course_visits[course][month - 1] = visits

        print(f"Course Visits: {course_visits}")
        print(f"Age Groups: {age_groups}")
        print(f"Place Visits: {place_visits}")
        print(f"Monthly Course Visits: {monthly_course_visits}")

        return render_template('admin_home.html',
                               course_visits=course_visits,
                               age_groups=age_groups,
                               place_visits=place_visits,
                               total_visitors=total_visitors,
                               logged_in_users=logged_in_users,
                               monthly_course_visits=monthly_course_visits)
    else:
        flash('Unauthorized access! Admins only.')
        return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, role='admin').first()

        if user and check_password_hash(user.password, password):
            session['admin'] = user.username
            flash('Admin logged in successfully!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/admin/manage_students', methods=['GET', 'POST'])
def manage_students():
    if 'admin' in session:
        if request.method == 'POST':
            if 'add' in request.form:
                new_student = Student(
                    id=request.form.get('id'),
                    first_name=request.form.get('first_name'),
                    middle_name=request.form.get('middle_name'),
                    last_name=request.form.get('last_name'),
                    course=request.form.get('course'),
                    age=request.form.get('age'),
                    barangay=request.form.get('Barangay'),
                    municipality=request.form.get('Municipality'),
                    province=request.form.get('Province'),
                )
                db.session.add(new_student)
                db.session.commit()
                flash('Student added successfully!')

            elif 'remove' in request.form:
                student_id = request.form.get('id')
                student = Student.query.get(student_id)
                if student:
                    db.session.delete(student)
                    db.session.commit()
                    flash(f'Student with ID {student_id} deleted successfully!')
                else:
                    flash('Student not found.')

            return redirect(url_for('manage_students'))

        students = Student.query.all()
        return render_template('admin_manage_students.html', students=students)
    else:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

@app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        try:
            student.first_name = request.form['firstName']
            student.middle_name = request.form['middleName']
            student.last_name = request.form['lastName']
            student.course = request.form['course']
            student.age = request.form['age']
            student.Barangay = request.form['Barangay']
            student.Municipality = request.form['Municipality']
            student.Province = request.form['Province']

            if 'image' in request.files and request.files['image'].filename != '':
                image_file = request.files['image']
                image_filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image_file.save(image_path)
                student.image = image_filename

            db.session.commit()
            flash('Student updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'danger')

        return redirect(url_for('manage_students'))

    return render_template('admin_edit_student.html', student=student)

if __name__ == "__main__":
    app.run(debug=True)
