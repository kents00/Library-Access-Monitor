from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import json
from config import Config
from models import db
from utils.export import export_attendance_csv, export_attendance_pdf

from dotenv import load_dotenv
load_dotenv()

# Import the backup function at the top of the file
from utils.backup import backup_deleted_records

# Create Flask app and configure
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

# Ensure upload directories exist
from utils.ensure_dirs import ensure_upload_directories
ensure_upload_directories(app)

# Import models - ensuring proper order for table creation
from models.location import Location
from models.course import Course
from models.user import User
from models.student import Student
from models.attendance import Attendance

# Import blueprints AFTER db initialization to avoid circular imports
from routes import student_bp, admin_bp, graph_bp

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(student_bp, url_prefix='/api')
app.register_blueprint(graph_bp, url_prefix='/api')

@app.route('/', methods=['GET', 'POST'])
def login():
    # Get current datetime to use in template
    now = datetime.datetime.now()

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request - forward to API and return JSON directly
            response = app.test_client().post('/api/', data=request.form)
            return response.data
        else:
            # Handle regular form submission
            student_id = request.form.get('id')

            # Make API call to student login endpoint through test client
            response = app.test_client().post('/api/', data={'id': student_id})
            data = json.loads(response.data)

            if not data.get('success'):
                flash(data.get('message', 'Error logging in'), 'error')

            # Add a script to close any open loading indicators
            return render_template('login.html', student=data.get('student'), close_loading=True, now=now)
    else:
        return render_template('login.html', student=None, now=now)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        flash('Unauthorized access! Admins only.')
        return redirect(url_for('admin_login'))

    # Handle regular page load - get data from API
    try:
        filter_type = request.args.get('filter', 'weekly')

        # Create a test client with preserved session context
        test_client = app.test_client()
        with test_client.session_transaction() as test_session:
            # Copy session data to test client session
            test_session['admin'] = session.get('admin')
            test_session['admin_image'] = session.get('admin_image')

        # Make the request with debug info
        app.logger.debug(f"Requesting API data with filter: {filter_type}")
        response = test_client.get(f'/api/admin?filter={filter_type}')

        # Check response status and content before parsing
        app.logger.debug(f"API response status: {response.status_code}")
        app.logger.debug(f"API response type: {type(response.data)}")
        app.logger.debug(f"API response length: {len(response.data) if response.data else 0}")

        # Only try parsing if we have data
        if response.data:
            data = json.loads(response.data)

            # Ensure we have all courses in the chart data
            if 'weekly_course_visits' not in data or not data['weekly_course_visits']:
                # Fallback: get all courses from database
                all_courses = Course.query.all()
                weekly_course_visits = {}
                for course in all_courses:
                    weekly_course_visits[course.course_name] = [0, 0, 0, 0, 0, 0, 0]
                data['weekly_course_visits'] = weekly_course_visits
                app.logger.info(f"Added fallback course data for {len(all_courses)} courses")

            # Process logged_in_users to make it compatible with the template
            logged_in_users_pairs = []
            if 'logged_in_users' in data:
                for user_data in data['logged_in_users']:
                    student_dict = user_data.get('student', {})
                    student = Student.query.get(student_dict.get('id'))
                    if student and 'login_time' in user_data and user_data['login_time']:
                        login_time = datetime.datetime.fromisoformat(user_data['login_time'])
                        logged_in_users_pairs.append((student, login_time))

            data['logged_in_users'] = logged_in_users_pairs

            # Get the admin user for the avatar display
            admin_username = session.get('admin')
            admin = User.query.filter_by(username=admin_username).first()
            data['admin'] = admin

            # Add timestamp for client-side real-time display
            data['server_timestamp'] = datetime.datetime.now().isoformat()

            # Ensure weekly_course_visits is properly formatted for JSON
            if 'weekly_course_visits' in data:
                # Log the data structure before rendering
                app.logger.debug(f"weekly_course_visits type: {type(data['weekly_course_visits'])}")
                app.logger.debug(f"weekly_course_visits courses: {list(data['weekly_course_visits'].keys())}")

                # Make sure it's already a dict (not a string)
                if isinstance(data['weekly_course_visits'], str):
                    data['weekly_course_visits'] = json.loads(data['weekly_course_visits'])

            return render_template('admin_new/ae_dashboard.html', **data)
        else:
            raise ValueError("Empty response from API")

    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        if 'response' in locals() and hasattr(response, 'data'):
            app.logger.error(f"Response content: {response.data}")

        # Get the admin user for the avatar display even in error case
        admin_username = session.get('admin')
        admin = User.query.filter_by(username=admin_username).first()

        # Provide default values with actual course names from database
        try:
            all_courses = Course.query.all()
            weekly_course_visits = {}
            for course in all_courses:
                weekly_course_visits[course.course_name] = [0, 0, 0, 0, 0, 0, 0]

            if not weekly_course_visits:
                # Ultimate fallback if no courses in database
                weekly_course_visits = {
                    'Information Technology': [0, 0, 0, 0, 0, 0, 0],
                    'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
                    'Home Economics': [0, 0, 0, 0, 0, 0, 0],
                    'Industrial Arts': [0, 0, 0, 0, 0, 0, 0],
                }
        except Exception as course_error:
            app.logger.error(f"Error fetching courses for fallback: {str(course_error)}")
            weekly_course_visits = {
                'Information Technology': [0, 0, 0, 0, 0, 0, 0],
                'Marine Biology': [0, 0, 0, 0, 0, 0, 0],
                'Home Economics': [0, 0, 0, 0, 0, 0, 0],
                'Industrial Arts': [0, 0, 0, 0, 0, 0, 0],
            }

        default_data = {
            'place_visits': [],
            'total_visitors': 0,
            'logged_in_users': [],
            'monthly_course_visits': {},
            'weekly_course_visits': weekly_course_visits,
            'weekly_place_visits': [],
            'monthly_place_visits': [],
            'top_weekly_places': [],
            'total_logins_month': 0,
            'login_percentage_increase': 0,
            'login_icon_class': 'ti-arrow-down-right text-danger',
            'login_bg_class': 'bg-light-danger',
            'top_weekly_place_visits_icon_class': 'ti-arrow-down-right text-danger',
            'top_weekly_place_visits_bg_class': 'bg-light-danger',
            'server_timestamp': datetime.datetime.now().isoformat(),
            'admin': admin
        }

        # Show a more user-friendly error
        flash(f'Could not load dashboard data. Please try again later. (Error: {str(e)})', 'error')
        return render_template('admin_new/ae_dashboard.html', **default_data)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Get the admin user
        user = User.query.filter_by(username=username, role='admin').first()

        if user and check_password_hash(user.password, password):
            session['admin'] = username
            # Also store the admin image in session if available
            if hasattr(user, 'image') and user.image:
                session['admin_image'] = user.image

            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Use consistent error category
            flash('Invalid username or password.', 'error')
            return render_template('admin_new/ae_login.html')

    return render_template('admin_new/ae_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully!', 'success')  # Added success category
    return redirect(url_for('login'))

@app.route('/admin/manage_students', methods=['GET', 'POST'])
def manage_students():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    # Handle the functionality directly instead of calling the blueprint
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

    # For GET requests, fetch the students directly
    try:
        students = Student.query.all()
        return render_template('admin_new/ae_manage.html', students=students)
    except Exception as e:
        app.logger.error(f"Error loading students: {str(e)}")
        flash(f"Error loading students: {str(e)}", 'danger')
        return render_template('admin_new/ae_manage.html', students=[])

@app.route('/admin/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    # Get student data directly from database
    student = Student.query.get_or_404(student_id)
    courses = Course.query.all()

    if request.method == 'POST':
        try:
            student.first_name = request.form['firstName']
            student.middle_name = request.form['middleName']
            student.last_name = request.form['lastName']
            student.age = request.form['age']
            student.course_id = request.form['course']

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
                from werkzeug.utils import secure_filename
                image_filename = secure_filename(image_file.filename)
                import os
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

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

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

            from werkzeug.utils import secure_filename
            import os

            image_file = request.files['image']
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('static/uploads', filename)
                image_file.save(image_path)
            else:
                filename = 'default_image.jpg'

            # Create the location first
            location = Location(
                barangay=barangay, municipality=municipality, province=province)
            db.session.add(location)
            db.session.flush()  # To get the location ID

            # Now create the student with the location ID
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
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')

    # Get courses for the form
    courses = Course.query.all()
    student = Student()  # Empty student object for the form
    return render_template('admin_new/ae_add_student.html', courses=courses, student=student)

@app.route('/admin/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        student = Student.query.get(student_id)
        if student:
            # Create backup before deletion
            backup_deleted_records('Student', [student])

            db.session.delete(student)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Student {student_id} deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Helper function for validating file uploads
def allowed_file(filename):
    allowed_extensions = {'gif', 'png', 'jpg', 'jpeg', 'bmp', 'webp', 'avif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/admin/download_records', methods=['GET', 'POST'])
def download_records():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    # Get the current admin from the database
    admin_username = session.get('admin')
    admin = User.query.filter_by(username=admin_username).first()

    if request.method == 'POST':
        # Process the form submission
        filter_type = request.form.get('filter', 'weekly')
        course_id = request.form.get('course')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')

        # Calculate date ranges similar to the blueprint function
        today = datetime.datetime.now()

        if filter_type == 'weekly':
            start_date = today - datetime.timedelta(weeks=1)
            end_date = today
        elif filter_type == 'monthly':
            start_date = today - datetime.timedelta(weeks=4)
            end_date = today
        elif filter_type == 'yearly':
            start_date = today - datetime.timedelta(weeks=52)
            end_date = today
        else:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else today - datetime.timedelta(weeks=1)
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else today

                if start_time_str:
                    start_date = start_date.replace(hour=int(start_time_str.split(':')[0]), minute=int(start_time_str.split(':')[1]))
                if end_time_str:
                    end_date = end_date.replace(hour=int(end_time_str.split(':')[0]), minute=int(end_time_str.split(':')[1]))
            except ValueError as e:
                flash(f'Error parsing dates: {str(e)}', 'danger')
                return redirect(url_for('download_records'))

        # Handle export actions
        if 'export_csv' in request.form:
            return export_attendance_csv(start_date, end_date, course_id)
        elif 'export_pdf' in request.form:
            return export_attendance_pdf(start_date, end_date, course_id)

    # For GET requests, just render the template with courses
    courses = Course.query.all()
    return render_template('admin_new/ae_download.html', courses=courses, admin=admin)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all locations - accessible for forms"""
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
        app.logger.error(f"Error getting locations: {str(e)}")
        return jsonify({'error': 'Failed to fetch locations'}), 500

@app.route('/download_graph')
def download_graph():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    try:
        weekly_course_visits = request.args.get('weekly_course_visits')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Add these parameters to the API call if provided
        params = {'weekly_course_visits': weekly_course_visits}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        response = app.test_client().get('/api/admin/download_graph', query_string=params)
        return response
    except Exception as e:
        app.logger.error(f"Download graph error: {str(e)}")
        flash(f"Error downloading graph: {str(e)}", 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage_admins', methods=['GET', 'POST'])
def manage_admins():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        try:
            # Handle form data directly instead of using test client
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
                    app.logger.debug(f"Image file selected: {image_file.filename}")
                else:
                    app.logger.debug("No valid image file selected")
            else:
                app.logger.debug("No image file in request")

            # Validate passwords
            if password and password != confirm_password:
                return jsonify({'success': False, 'message': 'Passwords do not match!'})

            # Get current admin for session validation
            admin_username = session.get('admin')
            current_admin = User.query.filter_by(username=admin_username, role='admin').first()

            if not current_admin:
                return jsonify({'success': False, 'message': 'Admin session invalid!'})

            try:
                if admin_id:
                    # Update existing admin
                    admin = User.query.get(admin_id)
                    if not admin:
                        return jsonify({'success': False, 'message': 'Admin not found!'})

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
                                from werkzeug.utils import secure_filename
                                import os

                                filename = secure_filename(image_file.filename)
                                uploads_dir = os.path.join(app.static_folder, 'uploads')

                                # Ensure uploads directory exists
                                if not os.path.exists(uploads_dir):
                                    os.makedirs(uploads_dir)
                                    app.logger.info(f"Created uploads directory: {uploads_dir}")

                                image_path = os.path.join(uploads_dir, filename)
                                image_file.save(image_path)
                                admin.image = filename
                                app.logger.info(f"Successfully saved image: {filename}")
                            else:
                                app.logger.warning(f"Invalid file type: {image_file.filename}")
                                return jsonify({'success': False, 'message': 'Invalid file type. Please use a valid image format.'})
                        except Exception as e:
                            app.logger.error(f"Error saving image: {str(e)}")
                            return jsonify({'success': False, 'message': f'Error saving image: {str(e)}'})

                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Admin updated successfully!'})
                else:
                    # Create new admin
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
                                from werkzeug.utils import secure_filename
                                import os

                                filename = secure_filename(image_file.filename)
                                uploads_dir = os.path.join(app.static_folder, 'uploads')

                                # Ensure uploads directory exists
                                if not os.path.exists(uploads_dir):
                                    os.makedirs(uploads_dir)

                                image_path = os.path.join(uploads_dir, filename)
                                image_file.save(image_path)
                                app.logger.info(f"Successfully saved new admin image: {filename}")
                            else:
                                app.logger.warning(f"Invalid file type for new admin: {image_file.filename}")
                                # Continue with default image
                                filename = 'admin_default.jpg'
                        except Exception as e:
                            app.logger.error(f"Error saving new admin image: {str(e)}")
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

            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Database error in admin management: {str(e)}")
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

        except Exception as e:
            app.logger.error(f"Error processing admin request: {str(e)}")
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

    # For GET requests, return admin data directly
    try:
        admin_username = session.get('admin')
        admin = User.query.filter_by(username=admin_username, role='admin').first()

        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found!'})

        locations = Location.query.all()

        return render_template('admin_new/ae_user.html',
                             admin=admin,
                             locations=[loc.to_dict() for loc in locations])
    except Exception as e:
        app.logger.error(f"Error loading admin data: {str(e)}")
        flash(f"Error loading admin data: {str(e)}", 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage_courses', methods=['GET', 'POST'])
def manage_courses():
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    # Forward to API endpoint
    test_client = app.test_client()
    with test_client.session_transaction() as test_session:
        test_session['admin'] = session.get('admin')
        test_session['admin_image'] = session.get('admin_image')

    if request.method == 'POST':
        response = test_client.post('/api/admin/manage_courses', data=request.form, content_type='application/x-www-form-urlencoded')
        return response.data
    else:
        response = test_client.get('/api/admin/manage_courses')
        return response.data

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'admin' not in session:
        flash('Unauthorized access!')
        return redirect(url_for('admin_login'))

    # Forward to API endpoint
    test_client = app.test_client()
    with test_client.session_transaction() as test_session:
        test_session['admin'] = session.get('admin')
        test_session['admin_image'] = session.get('admin_image')

    if request.method == 'POST':
        response = test_client.post(f'/api/admin/edit_course/{course_id}', data=request.form, content_type='application/x-www-form-urlencoded')
        return response.data
    else:
        response = test_client.get(f'/api/admin/edit_course/{course_id}')
        return response.data

@app.route('/admin/delete_course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    # Forward to API endpoint
    test_client = app.test_client()
    with test_client.session_transaction() as test_session:
        test_session['admin'] = session.get('admin')

    response = test_client.delete(f'/api/admin/delete_course/{course_id}')
    return response.data

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'], secret_key=app.config['SECRET_KEY'])

