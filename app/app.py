from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Student, Attendance, User
from datetime import datetime, timedelta
from flask import Response
import csv
import os

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
    student = None  # Initialize student as None to handle first-time visits

    if request.method == 'POST':
        # Get the ID entered by the user
        student_id = request.form['id']
        print(f"Student ID entered: {student_id}")

        # Query the student from the database
        student = Student.query.filter_by(id=student_id).first()

        if student:
            # If the student exists, record their attendance
            new_attendance = Attendance(student_id=student.id, check_in_time=datetime.now())
            db.session.add(new_attendance)
            db.session.commit()
        else:
            flash('Invalid ID. Please try again.')

    # Render the login page with the student information if available
    return render_template('login.html', student=student)



@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    # Check if admin is logged in
    if 'admin' in session:
        filter_type = request.form.get('filter') if request.method == 'POST' else 'weekly'
        
        # Get today's date for filtering
        today = datetime.now()

        # Calculate the date range based on the filter
        if filter_type == 'weekly':
            start_date = today - timedelta(weeks=1)
        elif filter_type == 'monthly':
            start_date = today - timedelta(weeks=4)  # Approximately 4 weeks
        elif filter_type == 'yearly':
            start_date = today - timedelta(weeks=52)  # Approximately 52 weeks

        if request.method == 'POST' and 'export_csv' in request.form:
            return export_attendance_csv(start_date)

        # Query attendance with student details within the specified date range
        attendance_data = db.session.query(Attendance, Student).join(Student, Attendance.student_id == Student.id).filter(Attendance.check_in_time >= start_date).all()

        # Analytics 1: Most visited library based on course
        course_visits = db.session.query(Student.course, db.func.count(Attendance.id).label('visits')).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.course).all()

        # Analytics 2: Age groups of visitors
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

        # Analytics 3: Students' place of residence
        place_visits = db.session.query(Student.place_of_residence, db.func.count(Attendance.id).label('visits')).join(Attendance).filter(Attendance.check_in_time >= start_date).group_by(Student.place_of_residence).all()

        return render_template('admin_dashboard.html', 
                                course_visits=course_visits, 
                                age_groups=age_groups, 
                                place_visits=place_visits)
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
                # Handle image upload
                image_file = request.files['image']
                image_filename = None
                if image_file:
                    image_filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                    image_file.save(image_path)  # Save the file

                # Add new student
                new_student = Student(
                    id=request.form.get('id'),
                    first_name=request.form.get('first_name'),
                    middle_name=request.form.get('middle_name'),
                    last_name=request.form.get('last_name'),
                    course=request.form.get('course'),
                    age=request.form.get('age'),
                    place_of_residence=request.form.get('place_of_residence'),
                    image=image_filename  # Store image file name
                )
                db.session.add(new_student)
                db.session.commit()
                flash('Student added successfully!')

            elif 'remove' in request.form:
                # Remove existing student
                student_id = request.form.get('id')
                student = Student.query.get(student_id)
                if student:
                    db.session.delete(student)
                    db.session.commit()
                    flash('Student removed successfully!')
                else:
                    flash('Student not found.')

            return redirect(url_for('manage_students'))

        students = Student.query.all()
        return render_template('manage_students.html', students=students)
    else:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error_code=404, error_message="Page not found."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('404.html', error_code=500, error_message="Internal server error."), 500

def handle_error(exception):
    # Log the exception or perform any specific error handling here
    return render_template('404.html', error_code=500, error_message=str(exception)), 500

if __name__ == '__main__':
    app.run(debug=True)