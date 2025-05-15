import os
import sqlalchemy
from datetime import datetime, timedelta
import json
import io
import matplotlib.pyplot as plt
from flask import redirect, url_for, flash, session, current_app, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db
from routes import admin_bp
from sqlalchemy import extract
from models.user import User
from models.course import Course
from models.student import Student
from models.attendance import Attendance
from models.location import Location
from utils.export import export_attendance_csv, export_attendance_pdf

def allowed_file(filename):
    allowed_extensions = {'gif', 'png', 'jpg', 'jpeg', 'bmp', 'webp', 'avif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Unauthorized access!')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    if 'admin' in session:
        try:
            filter_type = request.args.get('filter', 'weekly')

            # Get custom date parameters if provided
            start_date_str = request.args.get('startDate')
            end_date_str = request.args.get('endDate')

            today = datetime.now()

            # Determine date range based on filter or custom dates
            if start_date_str and end_date_str and filter_type == 'custom':
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Set end_date to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            elif filter_type == 'weekly':
                start_date = today - timedelta(weeks=1)
                end_date = today
            elif filter_type == 'monthly':
                start_date = today - timedelta(weeks=4)
                end_date = today
            elif filter_type == 'yearly':
                start_date = today - timedelta(weeks=52)
                end_date = today
            else:
                # Default to weekly if something goes wrong
                start_date = today - timedelta(weeks=1)
                end_date = today

            # Log the filter type and date range for debugging
            current_app.logger.debug(f"Filter: {filter_type}, Date range: {start_date} to {end_date}")

            if request.method == 'POST' and 'export_csv' in request.form:
                return export_attendance_csv(start_date)

            course_mapping = {
                course.id: course.course_name for course in Course.query.all()}

            # Debug query parameters
            current_app.logger.debug(f"Query parameters: {dict(request.args)}")

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

            # Modified: Get recent logins instead of using is_logged_in flag
            # Consider students who logged in within the last 24 hours as "logged in"
            recent_time = today - timedelta(hours=24)
            logged_in_users = db.session.query(Student, db.func.max(Attendance.check_in_time).label('login_time')).join(
                Attendance, Student.id == Attendance.student_id).filter(
                Attendance.check_in_time >= recent_time).group_by(Student.id).all()

            # Convert logged_in_users to serializable format
            logged_in_users_data = [
                {
                    'student': user[0].to_dict(),
                    'login_time': user[1].isoformat() if user[1] else None
                }
                for user in logged_in_users
            ]

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

            # Make sure we're returning valid JSON
            result = {
                'place_visits': place_visits,
                'total_visitors': total_visitors,
                'logged_in_users': logged_in_users_data,
                'monthly_course_visits': monthly_course_visits,
                'weekly_course_visits': weekly_course_visits,
                'weekly_place_visits': weekly_place_visits,
                'monthly_place_visits': monthly_place_visits,
                'top_weekly_places': top_weekly_places if top_weekly_places else [],
                'total_logins_month': total_logins_month,
                'login_percentage_increase': login_percentage_increase,
                'login_icon_class': login_icon_class,
                'login_bg_class': login_bg_class,
                'top_weekly_place_visits_icon_class': top_weekly_place_visits_icon_class,
                'top_weekly_place_visits_bg_class': top_weekly_place_visits_bg_class
            }

            # Add sanity check to make sure we're returning valid data
            current_app.logger.debug(f"API response data: {result}")

            # Return a proper JSON response
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f"Error in admin dashboard API: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Error generating dashboard data: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'message': 'Unauthorized access! Admins only.'
        }), 401

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
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
            # Also store the admin image in session if available
            if hasattr(user, 'image') and user.image:
                session['admin_image'] = user.image
            return jsonify({
                'success': True,
                'message': 'Admin logged in successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid username or password.'
            })

    return jsonify({'success': True})

@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully!')
    return redirect(url_for('admin_login'))

@admin_bp.route('/admin/manage_students', methods=['GET', 'POST'])
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

@admin_bp.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
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
                student.course_id = course_id

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
                        current_app.config['UPLOAD_FOLDER'], image_filename)
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

@admin_bp.route('/admin/add_student', methods=['GET', 'POST'])
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
                    course_id=course_id,
                    age=age,
                    image=filename,
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

@admin_bp.route('/admin/delete_student/<int:student_id>', methods=['DELETE'])
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

@admin_bp.route('/export/csv')
@admin_required
def export_csv():
    if 'admin' not in session:
        flash('Unauthorized access! Admins only.')
        return redirect(url_for('admin_login'))

    start_date = datetime.now() - timedelta(weeks=1)
    return export_attendance_csv(start_date)

@admin_bp.route('/export/pdf')
@admin_required
def export_pdf():
    if 'admin' not in session:
        flash('Unauthorized access! Admins only.')
        return redirect(url_for('admin_login'))

    start_date = datetime.now() - timedelta(weeks=1)
    return export_attendance_pdf(start_date)

@admin_bp.route('/admin/download_records', methods=['GET', 'POST'])
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

@admin_bp.route('/api/locations', methods=['GET'])
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

@admin_bp.route('/download_graph')
@admin_required
def download_graph():
    try:
        weekly_course_visits_str = request.args.get('weekly_course_visits')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not weekly_course_visits_str:
            current_app.logger.error("Missing weekly_course_visits parameter")
            return jsonify({'success': False, 'message': 'Missing data parameter'}), 400

        try:
            weekly_course_visits = json.loads(weekly_course_visits_str)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400

        fig, ax = plt.subplots(figsize=(10, 6))  # Larger figure size
        categories = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        # Add title with date range if provided
        title = 'Weekly Course Visits'
        if start_date and end_date:
            title += f' ({start_date} to {end_date})'

        ax.set_title(title, fontsize=14)

        for course, data in weekly_course_visits.items():
            ax.plot(categories, data, marker='o', linewidth=2, label=course)

        ax.set_xlabel('Day of the Week', fontsize=12)
        ax.set_ylabel('Visits', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='best', fontsize=10)

        # Enhanced styling
        plt.tight_layout()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Create timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'visitor_statistics_{timestamp}.png'

        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=120)
        img.seek(0)
        plt.close(fig)

        return send_file(img, mimetype='image/png', as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error in download_graph: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating graph: {str(e)}'}), 500

@admin_bp.route('/admin/manage_admins', methods=['GET', 'POST'])
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
                return jsonify({'success': False, 'message': 'Passwords do not match!'})

            try:
                if admin_id:
                    admin = User.query.get(admin_id)
                    if admin:
                        admin.username = username
                        admin.password = generate_password_hash(password)
                        if image_file and allowed_file(image_file.filename):
                            filename = secure_filename(image_file.filename)
                            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        image_file.save(image_path)
                        new_admin.image = filename
                    db.session.add(new_admin)
                    db.session.commit()
                    flash('Admin registered successfully!', 'success')
            except sqlalchemy.exc.OperationalError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Database error: Unable to save changes. Please try again later.'})

            return jsonify({'success': True, 'message': 'Admin settings updated successfully!'})

        # For GET requests, this data will be handled by the app route
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Unauthorized access!'})

@admin_bp.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "Admin blueprint is working correctly!"})