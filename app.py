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
                app.logger.debug(f"weekly_course_visits content sample: {str(data['weekly_course_visits'])[:100]}")

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

        # Provide default values for all variables used in the template
        default_data = {
            'place_visits': [],
            'total_visitors': 0,
            'logged_in_users': [],
            'monthly_course_visits': {},
            'weekly_course_visits': {
                'Information Technology': [0] * 7,
                'Marine Biology': [0] * 7,
                'Home Economics': [0] * 7,
                'Industrial Arts': [0] * 7,
            },
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
            return redirect(url_for('admin_dashboard'))
        else:
            # Pass error to template to be displayed with Notiflix
            return render_template('admin_new/ae_login.html', error='Invalid username or password.')

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
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    response = admin_bp.get_locations()
    return response

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
            # Create a new test client for the request
            test_client = app.test_client()

            # Common form data
            form_data = {key: request.form[key] for key in request.form}

            # Handle the API request first (without file)
            response = test_client.post(
                '/api/admin/manage_admins',
                data=form_data,
                content_type='multipart/form-data'
            )

            # Process file upload separately if a file was provided
            if 'profile_image' in request.files and request.files['profile_image'].filename:
                from werkzeug.utils import secure_filename
                import os

                # Create uploads directory if it doesn't exist
                uploads_dir = os.path.join(app.static_folder, 'uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)

                admin_id = request.form.get('adminId')
                image_file = request.files['profile_image']
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(uploads_dir, filename)
                image_file.save(image_path)

                # Update the admin's image in the database
                admin = User.query.get(admin_id) if admin_id else User.query.filter_by(role='admin').first()
                if admin:
                    admin.image = filename
                    db.session.commit()
                    app.logger.info(f"Updated admin image: {filename}")

            # Process the response
            data = response.get_json() if hasattr(response, 'get_json') else {}

            if data.get('success'):
                flash('Admin settings updated successfully!', 'success')
            elif 'message' in data:
                flash(data['message'], 'danger')

        except Exception as e:
            app.logger.error(f"Error processing admin request: {str(e)}")
            flash(f"An error occurred while updating admin settings: {str(e)}", 'danger')

    # Get the admin user for the form
    admin = User.query.filter_by(role='admin').first()
    return render_template('admin_new/ae_user.html', admin=admin)


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'], secret_key=app.config['SECRET_KEY'])

