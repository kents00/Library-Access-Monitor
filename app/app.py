from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from models import db, Student, Attendance, User, Location, Course
from flask_migrate import Migrate
from flask import Response, render_template, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import extract
from functools import wraps
from weasyprint import HTML
import os
import json
import matplotlib.pyplot as plt
import io
import sqlalchemy  # Import sqlalchemy

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///library.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)  # Initialize Flask-Migrate

    with app.app_context():
        db.create_all()

    UPLOAD_FOLDER = 'static/uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin' not in session:
                flash('Unauthorized access! Please log in as an admin.')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function


    def allowed_file(filename):
        allowed_extensions = {'gif', 'png', 'jpg', 'jpeg', 'bmp', 'webp', 'avif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


    def export_attendance_csv(start_date, end_date=None, course_id=None):
        query = db.session.query(Attendance, Student, Course.course_name).\
            join(Student, Attendance.student_id == Student.id).\
            join(Course, Student.course_id == Course.id).\
            filter(Attendance.check_in_time >= start_date)

        if end_date:
            query = query.filter(Attendance.check_in_time <= end_date)

        if course_id:
            query = query.filter(Course.id == course_id)

        attendance_data = query.all()

        def generate():
            yield "ID,First Name,Last Name,Course,Check-in Time\n"
            for attendance, student, course_name in attendance_data:
                check_in_time_24hr = attendance.check_in_time.strftime("%Y-%m-%d %H:%M:%S")
                yield f"{student.id},{student.first_name},{student.last_name},{course_name},{check_in_time_24hr}\n"

        return Response(generate(),
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=attendance_data.csv"})


    def export_attendance_pdf(start_date, end_date=None, course_id=None):
        query = db.session.query(Attendance, Student, Course.course_name).\
            join(Student, Attendance.student_id == Student.id).\
            join(Course, Student.course_id == Course.id).\
            filter(Attendance.check_in_time >= start_date)

        if end_date:
            query = query.filter(Attendance.check_in_time <= end_date)

        if course_id:
            query = query.filter(Course.id == course_id)

        attendance_data = query.all()

        rendered_html = render_template("pdf_template.html", attendance_data=attendance_data, datetime=datetime)
        pdf = HTML(string=rendered_html).write_pdf()

        return Response(pdf,
                        mimetype='application/pdf',
                        headers={"Content-Disposition": "attachment;filename=attendance_data.pdf"})


    @app.route('/', methods=['GET', 'POST'])
    def login():
        student = None

        if request.method == 'POST':
            student_id = request.form['id']
            print(f"Student ID entered: {student_id}")

            student = Student.query.filter_by(id=student_id).first()

            if student:
                new_attendance = Attendance(
                    student_id=student.id, check_in_time=datetime.now())
                db.session.add(new_attendance)
                student.is_logged_in = True
                db.session.commit()
            else:
                flash('No student ID number found. Please try again.')
        return render_template('login.html', student=student)


    @app.route('/admin', methods=['GET', 'POST'])
    @admin_required
    def admin_dashboard():
        if 'admin' in session:
            filter_type = request.form.get(
                'filter') if request.method == 'POST' else 'weekly'
            today = datetime.now()

            if filter_type == 'weekly':
                start_date = today - timedelta(weeks=1)
            elif filter_type == 'monthly':
                start_date = today - timedelta(weeks=4)
            elif filter_type == 'yearly':
                start_date = today - timedelta(weeks=52)

            if request.method == 'POST' and 'export_csv' in request.form:
                return export_attendance_csv(start_date)

            attendance_data = db.session.query(Attendance, Student).select_from(Attendance).join(
                Student, Attendance.student_id == Student.id).filter(Attendance.check_in_time >= start_date).all()

            course_visits_raw = (
                db.session.query(Student.course, db.func.count(
                    Attendance.id).label('visits'))
                .select_from(Attendance)
                .join(Student, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .group_by(Student.course)
                .all()
            )

            course_mapping = {
                course.id: course.course_name for course in Course.query.all()}

            place_visits_raw = (
                db.session.query(Location.municipality, db.func.count(
                    Attendance.id).label('visits'))
                .join(Student, Student.location_id == Location.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .group_by(Location.municipality)
                .all()
            )

            place_visits = [{"municipality": place, "visits": visits}
                            for place, visits in place_visits_raw]

            logged_in_users = db.session.query(Student, db.func.max(Attendance.check_in_time).label('login_time')).join(
                Attendance, Student.id == Attendance.student_id).filter(Student.is_logged_in == True).group_by(Student.id).all()

            total_visitors = db.session.query(Attendance.student_id).filter(
                Attendance.check_in_time >= start_date).distinct().count()

            course_visits_by_month = (
                db.session.query(
                    Course.course_name,
                    extract('month', Attendance.check_in_time).label('month'),
                    db.func.count(Attendance.id).label('visits')
                )
                .select_from(Student)
                .join(Course, Student.course_id == Course.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .group_by(Course.course_name, extract('month', Attendance.check_in_time))
                .all()
            )

            monthly_course_visits = {
                'Information Technology': [0] * 12,
                'Marine Biology': [0] * 12,
                'Home Economics': [0] * 12,
                'Industrial Arts': [0] * 12,
            }

            for course, month, visits in course_visits_by_month:
                if course in monthly_course_visits:
                    monthly_course_visits[course][month - 1] = visits

            weekly_course_visits = {
                'Information Technology': [0] * 7,
                'Marine Biology': [0] * 7,
                'Home Economics': [0] * 7,
                'Industrial Arts': [0] * 7,
            }

            course_visits_by_week = (
                db.session.query(
                    Course.course_name,
                    extract('dow', Attendance.check_in_time).label('day_of_week'),
                    db.func.count(Attendance.id).label('visits')
                )
                .select_from(Student)
                .join(Course, Student.course_id == Course.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .group_by(Course.course_name, extract('dow', Attendance.check_in_time))
                .all()
            )

            for course, day_of_week, visits in course_visits_by_week:
                if course in weekly_course_visits:
                    weekly_course_visits[course][day_of_week] = visits

            print(f"Place Visits: {place_visits}")
            print(f"Monthly Course Visits: {monthly_course_visits}")
            print(f"Weekly Course Visits: {weekly_course_visits}")


            # Calculate weekly place visits
            weekly_place_visits_raw = (
                db.session.query(Location.municipality, db.func.count(Attendance.id).label('visits'))
                .join(Student, Student.location_id == Location.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .group_by(Location.municipality)
                .all()
            )

            weekly_place_visits = [{"municipality": place, "visits": visits} for place, visits in weekly_place_visits_raw]
            weekly_place_visits.sort(key=lambda x: x['visits'], reverse=True)  # Sort by visits in descending order

            # Calculate monthly place visits
            monthly_place_visits_raw = (
                db.session.query(Location.municipality, db.func.count(Attendance.id).label('visits'))
                .join(Student, Student.location_id == Location.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= (today - timedelta(weeks=4)))
                .group_by(Location.municipality)
                .all()
            )

            monthly_place_visits = [{"municipality": place, "visits": visits} for place, visits in monthly_place_visits_raw]

            # Get the top two places for weekly visits
            top_weekly_places = sorted(weekly_place_visits, key=lambda x: x['visits'], reverse=True)[:2]

            # Ensure no None or Undefined values in weekly_course_visits
            for course in weekly_course_visits:
                weekly_course_visits[course] = [0 if v is None else v for v in weekly_course_visits[course]]

            # Ensure no None or Undefined values in course_mapping
            course_mapping = {k: (v if v is not None else "") for k, v in course_mapping.items()}

            # Calculate total log-ins in a month
            start_date_month = today - timedelta(weeks=4)
            total_logins_month = db.session.query(Attendance).filter(
                Attendance.check_in_time >= start_date_month).count()

            # Calculate percentage increase in log-ins compared to the previous month
            start_date_prev_month = start_date_month - timedelta(weeks=4)
            total_logins_prev_month = db.session.query(Attendance).filter(
                Attendance.check_in_time >= start_date_prev_month,
                Attendance.check_in_time < start_date_month).count()

            if total_logins_prev_month > 0:
                login_percentage_increase = ((total_logins_month - total_logins_prev_month) / total_logins_prev_month) * 100
                login_icon_class = "ti-arrow-up-left text-success" if total_logins_month > total_logins_prev_month else "ti-arrow-down-right text-danger"
                login_bg_class = "bg-light-success" if total_logins_month > total_logins_prev_month else "bg-light-danger"
            else:
                login_percentage_increase = 100  # Assume 100% increase if there were no log-ins in the previous month
                login_icon_class = "ti-arrow-up-left text-success"
                login_bg_class = "bg-light-success"

            # Determine if top weekly place visits are higher or lower
            if top_weekly_places:
                top_weekly_place_visits_icon_class = "ti-arrow-up-left text-success" if top_weekly_places[0]['visits'] > 0 else "ti-arrow-down-right text-danger"
                top_weekly_place_visits_bg_class = "bg-light-success" if top_weekly_places[0]['visits'] > 0 else "bg-light-danger"
            else:
                top_weekly_place_visits_icon_class = "ti-arrow-down-right text-danger"
                top_weekly_place_visits_bg_class = "bg-light-danger"

            return render_template('admin_new/ae_dashboard.html',
                                place_visits=place_visits,
                                total_visitors=total_visitors,
                                logged_in_users=logged_in_users,
                                monthly_course_visits=monthly_course_visits,
                                weekly_course_visits=weekly_course_visits,
                                weekly_place_visits=weekly_place_visits,
                                monthly_place_visits=monthly_place_visits,
                                top_weekly_places=top_weekly_places,
                                total_logins_month=total_logins_month,
                                login_percentage_increase=login_percentage_increase,
                                login_icon_class=login_icon_class,
                                login_bg_class=login_bg_class,
                                top_weekly_place_visits_icon_class=top_weekly_place_visits_icon_class,
                                top_weekly_place_visits_bg_class=top_weekly_place_visits_bg_class)
        else:
            flash('Unauthorized access! Admins only.')
            return redirect(url_for('admin_login'))


    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username, role='admin').first()

            if user:
                print(f"Stored hashed password: {user.password}")
                print(f"Password check: {check_password_hash(user.password, password)}")

            if user and check_password_hash(user.password, password):
                session['admin'] = user.username
                flash('Admin logged in successfully!')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password.')
                return redirect(url_for('admin_login'))

        return render_template('admin_new/ae_login.html')


    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin', None)
        flash('Logged out successfully!')
        return redirect(url_for('login'))


    @app.route('/admin/manage_students', methods=['GET', 'POST'])
    @admin_required
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
                        flash(
                            f'Student with ID {student_id} deleted successfully!')
                    else:
                        flash('Student not found.')

                return redirect(url_for('manage_students'))

            students = Student.query.all()
            return render_template('admin_new/ae_manage.html', students=students)
        else:
            flash('Unauthorized access!')
            return redirect(url_for('admin_login'))


    @app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
    @admin_required
    def edit_student(student_id):
        if 'admin' in session:
            student = Student.query.get_or_404(student_id)
            courses = Course.query.all()
            if request.method == 'POST':
                try:
                    student.first_name = request.form['firstName']
                    student.middle_name = request.form['middleName']
                    student.last_name = request.form['lastName']
                    student.age = request.form['age']

                    course_id = request.form['course']
                    student.course_id = course_id  # Ensure course_id is set correctly

                    location = Location.query.get(student.location_id)
                    if location:
                        location.barangay = request.form['Barangay']
                        location.municipality = request.form['Municipality']
                        location.province = request.form['Province']
                    else:
                        flash('Location not found.', 'danger')
                        return redirect(url_for('manage_students'))

                    if 'image' in request.files and request.files['image'].filename != '':
                        image_file = request.files['image']
                        image_filename = secure_filename(image_file.filename)
                        image_path = os.path.join(
                            app.config['UPLOAD_FOLDER'], image_filename)
                        image_file.save(image_path)
                        student.image = image_filename

                    db.session.commit()
                    flash('Student updated successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error updating student: {str(e)}', 'danger')

                return redirect(url_for('manage_students'))
            return render_template('admin_new/ae_manage_student.html', student=student, courses=courses)
        else:
            flash('Unauthorized access!')
            return redirect(url_for('admin_login'))


    @app.route('/admin/add_student', methods=['GET', 'POST'])
    @admin_required
    def add_student():
        if 'admin' in session:
            if request.method == 'POST':
                try:
                    student_id = request.form['studentId']
                    first_name = request.form['firstName']
                    middle_name = request.form['middleName']
                    last_name = request.form['lastName']
                    course_id = request.form['course']
                    age = request.form['age']
                    barangay = request.form['Barangay']
                    municipality = request.form['Municipality']
                    province = request.form['Province']

                    image_file = request.files['image']
                    if image_file and allowed_file(image_file.filename):
                        filename = secure_filename(image_file.filename)
                        image_path = os.path.join('static/uploads', filename)
                        image_file.save(image_path)
                    else:
                        filename = 'default_image.jpg'

                    location = Location(
                        barangay=barangay, municipality=municipality, province=province)
                    db.session.add(location)
                    db.session.commit()

                    student = Student(
                        id=student_id,
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                        course_id=course_id,  # Ensure course_id is set correctly
                        age=age,
                        image=filename,
                        is_logged_in=False,
                        location_id=location.id
                    )

                    db.session.add(student)
                    db.session.commit()
                    flash('Student added successfully!', 'success')
                    return redirect(url_for('manage_students'))
                except sqlalchemy.exc.OperationalError as e:
                    db.session.rollback()
                    flash('Database error: Unable to save changes. Please try again later.', 'danger')
                    return redirect(url_for('add_student'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error adding student: {str(e)}', 'danger')
                    return redirect(url_for('add_student'))

            try:
                courses = Course.query.all()
                student = Student()  # Pass an empty student object
                return render_template('admin_new/ae_add_student.html', courses=courses, student=student)
            except sqlalchemy.exc.OperationalError as e:
                flash('Database error: Unable to retrieve courses. Please try again later.', 'danger')
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Unauthorized access!')
            return redirect(url_for('admin_login'))


    @app.route('/admin/delete_student/<int:student_id>', methods=['DELETE'])
    @admin_required
    def delete_student(student_id):
        if 'admin' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Student {student_id} deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Student not found'}), 404


    @app.route('/export/csv')
    @admin_required
    def export_csv():
        if 'admin' not in session:
            flash('Unauthorized access! Admins only.')
            return redirect(url_for('admin_login'))

        start_date = datetime.now() - timedelta(weeks=1)
        return export_attendance_csv(start_date)


    @app.route('/export/pdf')
    @admin_required
    def export_pdf():
        if 'admin' not in session:
            flash('Unauthorized access! Admins only.')
            return redirect(url_for('admin_login'))

        start_date = datetime.now() - timedelta(weeks=1)
        return export_attendance_pdf(start_date)


    @app.route('/admin/download_records', methods=['GET', 'POST'])
    @admin_required
    def download_records():
        if 'admin' in session:
            filter_type = request.form.get('filter', 'weekly')
            course_id = request.form.get('course')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')

            today = datetime.now()

            if filter_type == 'weekly':
                start_date = today - timedelta(weeks=1)
                end_date = today
            elif filter_type == 'monthly':
                start_date = today - timedelta(weeks=4)
                end_date = today
            elif filter_type == 'yearly':
                start_date = today - timedelta(weeks=52)
                end_date = today
            else:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else today - timedelta(weeks=1)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else today

            if start_time_str:
                start_date = start_date.replace(hour=int(start_time_str.split(':')[0]), minute=int(start_time_str.split(':')[1]))
            if end_time_str:
                end_date = end_date.replace(hour=int(end_time_str.split(':')[0]), minute=int(end_time_str.split(':')[1]))

            if request.method == 'POST':
                if 'export_csv' in request.form:
                    return export_attendance_csv(start_date, end_date, course_id)
                elif 'export_pdf' in request.form:
                    return export_attendance_pdf(start_date, end_date, course_id)

            courses = Course.query.all()
            return render_template('admin_new/ae_download.html', courses=courses)
        else:
            flash('Unauthorized access! Admins only.')
            return redirect(url_for('admin_login'))


    @app.route('/api/locations', methods=['GET'])
    @admin_required
    def get_locations():
        province = request.args.get('province', '')
        municipality = request.args.get('municipality', '')

        filters = {}
        if province:
            filters['province'] = province
        if municipality:
            filters['municipality'] = municipality

        locations = Location.query.filter_by(**filters).all()

        location_data = [
            {
                'barangay': loc.barangay,
                'municipality': loc.municipality,
                'province': loc.province
            }
            for loc in locations
        ]
        return jsonify(location_data)


    @app.route('/download_graph')
    @admin_required
    def download_graph():
        weekly_course_visits = json.loads(request.args.get('weekly_course_visits'))

        fig, ax = plt.subplots()
        categories = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        for course, data in weekly_course_visits.items():
            ax.plot(categories, data, label=course)

        ax.set_xlabel('Day of the Week')
        ax.set_ylabel('Visits')
        ax.set_title('Weekly Course Visits')
        ax.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)

        return send_file(img, mimetype='image/png', as_attachment=True, download_name='visitor_statistics.png')


    @app.route('/admin/manage_admins', methods=['GET', 'POST'])
    @admin_required
    def manage_admins():
        if 'admin' in session:
            admin_id = request.form.get('adminId')
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                image_file = request.files.get('profile_image')

                if password != confirm_password:
                    flash('Passwords do not match!', 'danger')
                    return redirect(url_for('manage_admins'))

                try:
                    if admin_id:
                        admin = User.query.get(admin_id)
                        if admin:
                            admin.username = username
                            admin.password = generate_password_hash(password)
                            if image_file and allowed_file(image_file.filename):
                                filename = secure_filename(image_file.filename)
                                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                                image_file.save(image_path)
                                admin.image = filename
                            db.session.commit()
                            flash('Admin updated successfully!', 'success')
                        else:
                            flash('Admin not found!', 'danger')
                    else:
                        new_admin = User(
                            username=username,
                            password=generate_password_hash(password),
                            role='admin'
                        )
                        if image_file and allowed_file(image_file.filename):
                            filename = secure_filename(image_file.filename)
                            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            image_file.save(image_path)
                            new_admin.image = filename
                        db.session.add(new_admin)
                        db.session.commit()
                        flash('Admin registered successfully!', 'success')
                except sqlalchemy.exc.OperationalError as e:
                    db.session.rollback()
                    flash('Database error: Unable to save changes. Please try again later.', 'danger')
                    return redirect(url_for('manage_admins'))

                return redirect(url_for('manage_admins'))

            admin = User.query.filter_by(role='admin').first()
            return render_template('admin_new/ae_user.html', admin=admin)
        else:
            flash('Unauthorized access!')
            return redirect(url_for('admin_login'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
