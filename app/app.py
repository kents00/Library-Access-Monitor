from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from models import db, Student, Attendance, User
from datetime import datetime, timedelta
from sqlalchemy import extract
from weasyprint import HTML
import os
import csv

# Initialize the Flask app
app = Flask(__name__)

# Securely set configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///library.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with the app
db.init_app(app)

with app.app_context():
    db.create_all()

# File Uploads
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

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=attendance_data.csv"})

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    student = None
    if request.method == 'POST':
        student_id = request.form['id']
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
        # Filtering and dashboard data processing
        filter_type = request.form.get('filter') if request.method == 'POST' else 'weekly'
        today = datetime.now()
        start_date = today - timedelta(weeks={'weekly': 1, 'monthly': 4, 'yearly': 52}.get(filter_type, 1))

        if request.method == 'POST' and 'export_csv' in request.form:
            return export_attendance_csv(start_date)

        # Query data
        attendance_data = db.session.query(Attendance, Student).join(Student).filter(Attendance.check_in_time >= start_date).all()
        course_visits_raw = db.session.query(Student.course, db.func.count(Attendance.id).label('visits')).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.course).all()
        age_groups = {'Under 18': 0, '18-25': 0, '26-35': 0, '36-50': 0, 'Above 50': 0}
        for attendance, student in attendance_data:
            # Age group distribution
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

        # Process other dashboard data (similar to your original code)
        course_visits = [{"course": course, "visits": visits} for course, visits in course_visits_raw]

        return render_template('admin_home.html',
                               course_visits=course_visits,
                               age_groups=age_groups)
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

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=os.getenv("PORT", 5000))
