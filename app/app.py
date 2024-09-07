from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Attendance, User
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db.init_app(app)

# Create the database
with app.app_context():
    db.create_all()

### Routes and View Functions ###

# Route for the login page


@app.route('/', methods=['GET', 'POST'])
def login():
    student = None  # Initialize student as None to handle first-time visits

    if request.method == 'POST':
        # Get the ID entered by the user
        student_id = request.form['id']

        # Query the student from the database
        student = Student.query.filter_by(id=student_id).first()

        if student:
            # If the student exists, record their attendance
            new_attendance = Attendance(
                student_id=student.id, check_in_time=datetime.now())
            db.session.add(new_attendance)
            db.session.commit()
        else:
            flash('Invalid ID. Please try again.')

    # Render the login page with the student information if available
    return render_template('login.html', student=student)

# Route for the admin dashboard

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    # Check if admin is logged in
    if 'admin' in session:
        # Metrics calculation
        daily_count = Attendance.query.count()
        # Calculate more metrics as needed

        return render_template('admin_dashboard.html', daily_count=daily_count)
    else:
        flash('Unauthorized access! Admins only.')
        return redirect(url_for('login'))

# Route to handle admin login


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

# Route for admin logout


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# Admin can add or remove students


@app.route('/admin/manage_students', methods=['GET', 'POST'])
def manage_students():
    if 'admin' in session:
        if request.method == 'POST':
            # Handle adding or removing students
            if 'add' in request.form:
                # Add new student
                new_student = Student(
                    id=request.form.get('id'),
                    name=request.form.get('name'),
                    course=request.form.get('course'),
                    age=request.form.get('age'),
                    place_of_residence=request.form.get('place_of_residence')
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
        return redirect(url_for('login'))


### Application Entry Point ###
if __name__ == '__main__':
    app.run(debug=True)
