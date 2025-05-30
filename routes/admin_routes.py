import os
import sqlalchemy
from datetime import datetime, timedelta
import json
import io
import matplotlib.pyplot as plt
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import redirect, url_for, flash, session, current_app, request, jsonify, send_file, render_template
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
from utils.backup import backup_deleted_records  # Add this import
from utils.email_verification import (
    generate_verification_code,
    send_verification_email,
    store_verification_code,
    verify_code,
    cleanup_verification_code,
    is_verification_valid
)

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
                start_date = today - timedelta(weeks=1)
                end_date = today

            # Log the filter type and date range for debugging
            current_app.logger.debug(f"Filter: {filter_type}, Date range: {start_date} to {end_date}")

            if request.method == 'POST' and 'export_csv' in request.form:
                return export_attendance_csv(start_date, end_date)

            # Get all courses first to ensure all are included in chart data
            all_courses = Course.query.all()
            current_app.logger.debug(f"Found {len(all_courses)} courses in database")

            # Initialize weekly course visits with all available courses
            weekly_course_visits = {}
            for course in all_courses:
                weekly_course_visits[course.course_name] = [0, 0, 0, 0, 0, 0, 0]
                current_app.logger.debug(f"Initialized course: {course.course_name}")

            # Query attendance data grouped by course and day of week
            attendance_by_course_day = (
                db.session.query(
                    Course.course_name,
                    extract('dow', Attendance.check_in_time).label('day_of_week'),
                    db.func.count(Attendance.id).label('visit_count')
                )
                .join(Student, Student.id == Attendance.student_id)
                .join(Course, Course.id == Student.course_id)
                .filter(Attendance.check_in_time >= start_date)
                .filter(Attendance.check_in_time <= end_date)
                .group_by(Course.course_name, extract('dow', Attendance.check_in_time))
                .all()
            )

            current_app.logger.debug(f"Found {len(attendance_by_course_day)} attendance records")

            # Populate the weekly course visits data
            for course_name, day_of_week, visit_count in attendance_by_course_day:
                if course_name in weekly_course_visits:
                    # Convert PostgreSQL day of week (0=Sunday) to array index
                    day_index = int(day_of_week)
                    weekly_course_visits[course_name][day_index] = visit_count
                    current_app.logger.debug(f"Updated {course_name} day {day_index}: {visit_count} visits")

            # Log final chart data
            current_app.logger.debug(f"Final weekly_course_visits: {weekly_course_visits}")

            # Get place visits data
            place_visits_raw = (
                db.session.query(Location.municipality, db.func.count(
                    Attendance.id).label('visits'))
                .join(Student, Student.location_id == Location.id)
                .join(Attendance, Attendance.student_id == Student.id)
                .filter(Attendance.check_in_time >= start_date)
                .filter(Attendance.check_in_time <= end_date)
                .group_by(Location.municipality)
                .order_by(db.func.count(Attendance.id).desc())
                .all()
            )

            place_visits = [{"municipality": place, "visits": visits}
                            for place, visits in place_visits_raw]

            # Get recent logins (students who logged in within the last 24 hours)
            recent_time = today - timedelta(hours=24)

            recent_logins = (
                db.session.query(Attendance, Student)
                .join(Student, Student.id == Attendance.student_id)
                .filter(Attendance.check_in_time >= recent_time)
                .order_by(Attendance.check_in_time.desc())
                .limit(10)
                .all()
            )

            logged_in_users = []
            for attendance, student in recent_logins:
                logged_in_users.append({
                    'student': student.to_dict(),
                    'login_time': attendance.check_in_time.isoformat()
                })

            # Calculate statistics
            total_visitors = db.session.query(db.func.count(Attendance.id)).filter(
                Attendance.check_in_time >= start_date,
                Attendance.check_in_time <= end_date
            ).scalar() or 0

            # Calculate monthly logins
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total_logins_month = db.session.query(db.func.count(Attendance.id)).filter(
                Attendance.check_in_time >= month_start
            ).scalar() or 0

            # Calculate percentage increase (simplified)
            prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
            prev_month_logins = db.session.query(db.func.count(Attendance.id)).filter(
                Attendance.check_in_time >= prev_month_start,
                Attendance.check_in_time < month_start
            ).scalar() or 1

            login_percentage_increase = round(
                ((total_logins_month - prev_month_logins) / prev_month_logins) * 100, 1
            ) if prev_month_logins > 0 else 0

            # Set icon classes based on increase/decrease
            if login_percentage_increase >= 0:
                login_icon_class = 'ti-arrow-up-left text-success'
                login_bg_class = 'bg-light-success'
            else:
                login_icon_class = 'ti-arrow-down-right text-danger'
                login_bg_class = 'bg-light-danger'

            # Top places logic
            top_weekly_places = place_visits[:2] if place_visits else []

            if top_weekly_places:
                top_weekly_place_visits_icon_class = 'ti-arrow-up-left text-success'
                top_weekly_place_visits_bg_class = 'bg-light-success'
            else:
                top_weekly_place_visits_icon_class = 'ti-arrow-down-right text-danger'
                top_weekly_place_visits_bg_class = 'bg-light-danger'

            return jsonify({
                'success': True,
                'weekly_course_visits': weekly_course_visits,
                'logged_in_users': logged_in_users,
                'total_visitors': total_visitors,
                'total_logins_month': total_logins_month,
                'login_percentage_increase': login_percentage_increase,
                'login_icon_class': login_icon_class,
                'login_bg_class': login_bg_class,
                'top_weekly_places': top_weekly_places,
                'top_weekly_place_visits_icon_class': top_weekly_place_visits_icon_class,
                'top_weekly_place_visits_bg_class': top_weekly_place_visits_bg_class,
                'place_visits': place_visits,
                'filter_type': filter_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })

        except Exception as e:
            current_app.logger.error(f"Dashboard error: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Error loading dashboard data: {str(e)}',
                'weekly_course_visits': {},
                'logged_in_users': [],
                'total_visitors': 0,
                'total_logins_month': 0
            }), 500
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

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

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Admin logged in successfully!'
                })
            else:
                # Regular form submission - redirect to dashboard
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
        else:
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password.'
                })
            else:
                # Regular form submission - show error and return template
                flash('Invalid username or password.', 'error')
                return render_template('admin_new/ae_login.html')

    return render_template('admin_new/ae_login.html')

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

# Move this to be a standalone function that can be imported
def get_all_locations():
    """Get all locations - utility function"""
    try:
        locations = Location.query.all()
        location_data = [
            {
                'id': loc.id,
                'barangay': loc.barangay,
                'municipality': loc.municipality,
                'province': loc.province
            }
            for loc in locations
        ]
        return location_data
    except Exception as e:
        current_app.logger.error(f"Error getting locations: {str(e)}")
        return []

@admin_bp.route('/api/locations', methods=['GET', 'POST'])
def get_locations():
    """Get all locations or create a new location"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            barangay = data.get('barangay')
            municipality = data.get('municipality')
            province = data.get('province')

            if not all([barangay, municipality, province]):
                return jsonify({'success': False, 'message': 'All location fields are required'}), 400

            # Check if location already exists
            existing_location = Location.query.filter_by(
                barangay=barangay,
                municipality=municipality,
                province=province
            ).first()

            if existing_location:
                return jsonify({
                    'success': True,
                    'location_id': existing_location.id,
                    'message': 'Location already exists'
                })

            # Create new location
            new_location = Location(
                barangay=barangay,
                municipality=municipality,
                province=province
            )
            db.session.add(new_location)
            db.session.commit()

            return jsonify({
                'success': True,
                'location_id': new_location.id,
                'message': 'Location created successfully'
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating location: {str(e)}")
            return jsonify({'success': False, 'message': f'Error creating location: {str(e)}'}), 500

    else:  # GET request
        try:
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
                    'id': loc.id,
                    'barangay': loc.barangay,
                    'municipality': loc.municipality,
                    'province': loc.province
                }
                for loc in locations
            ]
            return jsonify(location_data)
        except Exception as e:
            current_app.logger.error(f"Error getting locations: {str(e)}")
            return jsonify({'error': 'Failed to fetch locations'}), 500

@admin_bp.route('/admin/api/locations', methods=['GET'])
@admin_required
def get_admin_locations():
    """Admin-only endpoint for locations with additional filtering"""
    return get_locations()  # Reuse the same logic

@admin_bp.route('/download_graph', methods=['GET', 'POST'])
@admin_required
def download_graph():
    try:
        # Process either GET or POST parameters
        if request.method == 'POST':
            weekly_course_visits_str = request.form.get('weekly_course_visits')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
        else:  # GET
            weekly_course_visits_str = request.args.get('weekly_course_visits')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

        if not weekly_course_visits_str:
            current_app.logger.error("Missing weekly_course_visits parameter")
            return jsonify({'success': False, 'message': 'Missing data parameter'}), 400

        # Import here to avoid circular imports
        from utils.graph_export import generate_visitor_statistics_graph

        # Generate and return the graph
        return generate_visitor_statistics_graph(weekly_course_visits_str, start_date, end_date)
    except Exception as e:
        current_app.logger.error(f"Error in download_graph: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating graph: {str(e)}'}), 500

@admin_bp.route('/admin/manage_admins', methods=['GET', 'POST'])
@admin_required
def manage_admins():
    if 'admin' in session:
        if request.method == 'POST':
            admin_id = request.form.get('adminId')
            username = request.form.get('username')
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            location_id = request.form.get('location_id')

            # Enhanced image file handling with multiple safety checks
            image_file = None
            if request.files and 'profile_image' in request.files:
                uploaded_file = request.files['profile_image']
                # Multiple checks: file exists, has filename, and filename is not empty
                if uploaded_file and hasattr(uploaded_file, 'filename') and uploaded_file.filename and uploaded_file.filename.strip():
                    image_file = uploaded_file
                    current_app.logger.debug(f"Image file selected: {image_file.filename}")
                else:
                    current_app.logger.debug("No valid image file selected")
            else:
                current_app.logger.debug("No image file in request")

            if password and password != confirm_password:
                return jsonify({'success': False, 'message': 'Passwords do not match!'})

            try:
                if admin_id:
                    admin = User.query.get(admin_id)
                    if admin:
                        admin.username = username
                        admin.email = email
                        admin.first_name = first_name
                        admin.last_name = last_name
                        admin.phone = phone
                        admin.location_id = location_id
                        if password:  # Only update password if provided
                            admin.password = generate_password_hash(password)

                        # Handle image upload with comprehensive error checking
                        if image_file:
                            try:
                                if allowed_file(image_file.filename):
                                    filename = secure_filename(image_file.filename)

                                    # Ensure upload folder exists
                                    uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                                    if not os.path.exists(uploads_dir):
                                        os.makedirs(uploads_dir)

                                    image_path = os.path.join(uploads_dir, filename)
                                    image_file.save(image_path)
                                    admin.image = filename
                                    current_app.logger.info(f"Successfully saved image: {filename}")
                                else:
                                    current_app.logger.warning(f"Invalid file type: {image_file.filename}")
                                    return jsonify({'success': False, 'message': 'Invalid file type. Please use a valid image format.'})
                            except Exception as e:
                                current_app.logger.error(f"Error saving image: {str(e)}")
                                return jsonify({'success': False, 'message': f'Error saving image: {str(e)}'})

                        db.session.commit()
                        return jsonify({'success': True, 'message': 'Admin updated successfully!'})
                    else:
                        return jsonify({'success': False, 'message': 'Admin not found!'})
                else:
                    # Create new admin
                    # Check if username or email already exists
                    existing_user = User.query.filter(
                        (User.username == username) | (User.email == email)
                    ).first()

                    if existing_user:
                        return jsonify({'success': False, 'message': 'Username or email already exists!'})

                    # Set default image
                    filename = 'admin_default.jpg'

                    # Handle image upload for new admin
                    if image_file:
                        try:
                            if allowed_file(image_file.filename):
                                filename = secure_filename(image_file.filename)

                                # Ensure upload folder exists
                                uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                                if not os.path.exists(uploads_dir):
                                    os.makedirs(uploads_dir)

                                image_path = os.path.join(uploads_dir, filename)
                                image_file.save(image_path)
                                current_app.logger.info(f"Successfully saved new admin image: {filename}")
                            else:
                                current_app.logger.warning(f"Invalid file type for new admin: {image_file.filename}")
                                # Continue with default image
                                filename = 'admin_default.jpg'
                        except Exception as e:
                            current_app.logger.error(f"Error saving new admin image: {str(e)}")
                            # Continue with default image if upload fails
                            filename = 'admin_default.jpg'

                    new_admin = User(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        password=generate_password_hash(password),
                        role='admin',
                        location_id=location_id,
                        image=filename
                    )
                    db.session.add(new_admin)
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Admin registered successfully!'})

            except sqlalchemy.exc.IntegrityError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Username or email already exists!'})
            except sqlalchemy.exc.OperationalError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Database error: Unable to save changes. Please try again later.'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})

        # For GET requests, return admin data and locations for the form
        admin_username = session.get('admin')
        current_admin = User.query.filter_by(username=admin_username, role='admin').first()
        locations = Location.query.all()

        return jsonify({
            'success': True,
            'admin': current_admin.to_dict() if current_admin else None,
            'locations': [location.to_dict() for location in locations]
        })
    else:
        return jsonify({'success': False, 'message': 'Unauthorized access!'})

@admin_bp.route('/admin/user_management', methods=['GET', 'POST'])
@admin_required
def user_management():
    """Allow users to manage their assigned students, courses, and locations"""
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    # Get current admin user
    admin_username = session.get('admin')
    current_user = User.query.filter_by(username=admin_username, role='admin').first()

    if not current_user:
        return jsonify({'success': False, 'message': 'Admin user not found'}), 404

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'assign_student':
            student_id = request.form.get('student_id')
            student = Student.query.get(student_id)
            if student:
                student.managed_by_user_id = current_user.id
                db.session.commit()
                return jsonify({'success': True, 'message': 'Student assigned successfully'})

        elif action == 'assign_course':
            course_id = request.form.get('course_id')
            course = Course.query.get(course_id)
            if course:
                course.managed_by_user_id = current_user.id
                db.session.commit()
                return jsonify({'success': True, 'message': 'Course assigned successfully'})

    # Get data for GET requests
    managed_students = Student.query.filter_by(managed_by_user_id=current_user.id).all()
    managed_courses = Course.query.filter_by(managed_by_user_id=current_user.id).all()
    unassigned_students = Student.query.filter_by(managed_by_user_id=None).all()
    unassigned_courses = Course.query.filter_by(managed_by_user_id=None).all()

    return jsonify({
        'success': True,
        'managed_students': [student.to_dict() for student in managed_students],
        'managed_courses': [course.to_dict() for course in managed_courses],
        'unassigned_students': [student.to_dict() for student in unassigned_students],
        'unassigned_courses': [course.to_dict() for course in unassigned_courses]
    })

@admin_bp.route('/admin/edit_managed_student/<student_id>', methods=['POST'])
@admin_required
def edit_managed_student(student_id):
    """Allow user to edit students they manage"""
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    admin_username = session.get('admin')
    current_user = User.query.filter_by(username=admin_username, role='admin').first()

    student = Student.query.filter_by(id=student_id, managed_by_user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found or not managed by you'}), 404

    try:
        student.first_name = request.form.get('first_name', student.first_name)
        student.middle_name = request.form.get('middle_name', student.middle_name)
        student.last_name = request.form.get('last_name', student.last_name)
        student.age = request.form.get('age', student.age)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Student updated successfully', 'student': student.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating student: {str(e)}'}), 500

@admin_bp.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "Admin blueprint is working correctly!"})

# Password reset routes
@admin_bp.route('/admin/forgot-password', methods=['GET', 'POST'])
def admin_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Please enter your email address.', 'warning')
            return render_template('admin_new/ae_forgot_password.html')

        # Check if admin with this email exists
        admin = User.query.filter_by(email=email, role='admin').first()

        if not admin:
            flash('No admin account found with this email address.', 'danger')
            return render_template('admin_new/ae_forgot_password.html')

        # Generate verification code
        verification_code = generate_verification_code()

        # Store code with timestamp
        store_verification_code(email, verification_code)

        # Send email
        email_sent = send_verification_email(email, verification_code)

        if email_sent:
            # Check if we have proper email configuration
            if current_app.config.get('MAIL_USERNAME') and current_app.config.get('MAIL_PASSWORD'):
                flash('Verification code sent to your email address. Please check your inbox.', 'success')
            else:
                # In development without email config, show the code
                if current_app.config.get('DEBUG', False):
                    flash(f'DEBUG MODE: Email not configured. Your verification code is: {verification_code}', 'info')
                else:
                    flash('Email service not configured. Please contact system administrator.', 'warning')

            return redirect(url_for('admin.admin_verify_code', email=email))
        else:
            flash('Failed to send verification code. Please try again later or contact support.', 'danger')
            return render_template('admin_new/ae_forgot_password.html')

    return render_template('admin_new/ae_forgot_password.html')

@admin_bp.route('/admin/verify-code')
def admin_verify_code():
    email = request.args.get('email')
    if not email:
        flash('Invalid request.', 'danger')
        return redirect(url_for('admin.admin_forgot_password'))

    return render_template('admin_new/ae_verify_code.html', email=email)

@admin_bp.route('/admin/verify-code', methods=['POST'])
def admin_verify_code_post():
    email = request.form.get('email')

    # Get individual code digits and combine them
    code_digits = []
    for i in range(1, 7):
        digit = request.form.get(f'code{i}', '')
        code_digits.append(digit)

    # Also check for the full code (fallback)
    entered_code = request.form.get('verification_code', ''.join(code_digits))

    if not email or not entered_code:
        flash('Please enter the complete verification code.', 'warning')
        return render_template('admin_new/ae_verify_code.html', email=email)

    # Verify the code using the utility function
    is_valid, message = verify_code(email, entered_code)

    if is_valid:
        # Code is correct, redirect to password reset
        return redirect(url_for('admin.admin_reset_password', email=email))
    else:
        flash(message, 'warning' if 'remaining' in message else 'danger')
        if 'request a new' in message:
            return redirect(url_for('admin.admin_forgot_password'))
        return render_template('admin_new/ae_verify_code.html', email=email)

@admin_bp.route('/admin/resend-code', methods=['POST'])
def admin_resend_code():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})

        # Check if admin exists
        admin = User.query.filter_by(email=email, role='admin').first()
        if not admin:
            return jsonify({'success': False, 'message': 'Invalid email address'})

        # Generate new verification code
        verification_code = generate_verification_code()

        # Store the new code
        store_verification_code(email, verification_code)

        # Send email
        if send_verification_email(email, verification_code):
            return jsonify({'success': True, 'message': 'Verification code resent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send verification code'})

    except Exception as e:
        current_app.logger.error(f"Error resending code: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/reset-password')
def admin_reset_password():
    email = request.args.get('email')
    if not email:
        flash('Invalid request.', 'danger')
        return redirect(url_for('admin.admin_forgot_password'))

    # Verify that the user completed the verification process
    if not is_verification_valid(email):
        flash('Session expired. Please start the password reset process again.', 'danger')
        return redirect(url_for('admin.admin_forgot_password'))

    return render_template('admin_new/ae_reset_password.html', email=email)

@admin_bp.route('/admin/reset-password', methods=['POST'])
def admin_reset_password_post():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not all([email, password, confirm_password]):
        flash('All fields are required.', 'warning')
        return render_template('admin_new/ae_reset_password.html', email=email)

    if password != confirm_password:
        flash('Passwords do not match.', 'warning')
        return render_template('admin_new/ae_reset_password.html', email=email)

    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'warning')
        return render_template('admin_new/ae_reset_password.html', email=email)

    # Verify session is still valid
    if not is_verification_valid(email):
        flash('Session expired. Please start the password reset process again.', 'danger')
        return redirect(url_for('admin.admin_forgot_password'))

    try:
        # Find and update admin password
        admin = User.query.filter_by(email=email, role='admin').first()
        if not admin:
            flash('Admin account not found.', 'danger')
            return redirect(url_for('admin.admin_forgot_password'))

        # Update password
        admin.password = generate_password_hash(password)
        db.session.commit()

        # Clean up verification code
        cleanup_verification_code(email)

        flash('Password reset successfully. You can now log in with your new password.', 'success')
        return redirect(url_for('admin.admin_login'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting password: {str(e)}")
        flash('An error occurred while resetting your password. Please try again.', 'danger')
        return render_template('admin_new/ae_reset_password.html', email=email)

@admin_bp.route('/admin/manage_courses', methods=['GET', 'POST'])
@admin_required
def manage_courses():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

    if request.method == 'POST':
        try:
            course_name = request.form.get('course_name')
            if not course_name:
                return jsonify({'success': False, 'message': 'Course name is required'}), 400

            # Check if course already exists
            existing_course = Course.query.filter_by(course_name=course_name).first()
            if existing_course:
                return jsonify({'success': False, 'message': 'Course already exists'}), 400

            # Create new course
            new_course = Course(course_name=course_name)
            db.session.add(new_course)
            db.session.commit()

            current_app.logger.info(f"Added new course: {course_name}")
            return jsonify({'success': True, 'message': 'Course added successfully', 'course': new_course.to_dict()})

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding course: {str(e)}")
            return jsonify({'success': False, 'message': f'Error adding course: {str(e)}'}), 500

    # GET request - return courses data
    try:
        courses = Course.query.all()
        courses_data = []

        for course in courses:
            student_count = Student.query.filter_by(course_id=course.id).count()
            course_dict = course.to_dict()
            course_dict['student_count'] = student_count
            courses_data.append(course_dict)

        current_app.logger.debug(f"Returning {len(courses_data)} courses")
        return render_template('admin_new/ae_manage_courses.html', courses=courses_data)
    except Exception as e:
        current_app.logger.error(f"Error loading courses: {str(e)}")
        flash(f"Error loading courses: {str(e)}", 'danger')
        return render_template('admin_new/ae_manage_courses.html', courses=[])

@admin_bp.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        try:
            course_name = request.form.get('course_name')
            if not course_name:
                return jsonify({'success': False, 'message': 'Course name is required'}), 400

            # Check if another course with the same name exists
            existing_course = Course.query.filter(
                Course.course_name == course_name,
                Course.id != course_id
            ).first()

            if existing_course:
                return jsonify({'success': False, 'message': 'Course name already exists'}), 400

            course.course_name = course_name
            db.session.commit()

            return jsonify({'success': True, 'message': 'Course updated successfully!'})

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating course: {str(e)}")
            return jsonify({'success': False, 'message': f'Error updating course: {str(e)}'}), 500

    # GET request - get course data and enrolled students
    try:
        enrolled_students = Student.query.filter_by(course_id=course.id).all()
        students_data = [student.to_dict() for student in enrolled_students]

        return render_template('admin_new/ae_edit_course.html',
                             course=course.to_dict(),
                             enrolled_students=students_data)
    except Exception as e:
        current_app.logger.error(f"Error loading course data: {str(e)}")
        flash(f"Error loading course data: {str(e)}", 'danger')
        return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/admin/delete_course/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'message': 'Course not found'}), 404

        # Check if there are students enrolled in this course
        student_count = Student.query.filter_by(course_id=course_id).count()
        if student_count > 0:
            return jsonify({'success': False, 'message': f'Cannot delete course. {student_count} students are enrolled in this course.'}), 400

        # Create backup before deletion
        backup_deleted_records('Course', [course])

        db.session.delete(course)
        db.session.commit()

        return jsonify({'success': True, 'message': f'Course "{course.course_name}" deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting course: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting course: {str(e)}'}), 500

@admin_bp.route('/admin/course_students/<int:course_id>', methods=['GET'])
@admin_required
def get_course_students(course_id):
    """Get all students enrolled in a specific course"""
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        course = Course.query.get_or_404(course_id)
        students = Student.query.filter_by(course_id=course_id).all()

        students_data = []
        for student in students:
            student_data = student.to_dict()
            # Add recent attendance info
            recent_attendance = Attendance.query.filter_by(student_id=student.id)\
                .order_by(Attendance.check_in_time.desc()).first()

            if recent_attendance:
                student_data['last_visit'] = recent_attendance.check_in_time.isoformat()
            else:
                student_data['last_visit'] = None

            students_data.append(student_data)

        return jsonify({
            'success': True,
            'course': course.to_dict(),
            'students': students_data
        })

    except Exception as e:
        current_app.logger.error(f"Error getting course students: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting course students: {str(e)}'}), 500