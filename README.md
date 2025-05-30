# Library Attendance Management

A modern web-based library attendance system built with Flask, designed to streamline student attendance management in libraries. This application provides an intuitive interface for students to check in via ID and offers comprehensive admin tools for viewing attendance metrics, generating reports, and managing user data.

![image](https://github.com/user-attachments/assets/bdd128d3-d202-453c-a68f-33d7b51e199f)

## 🚀 Features

### Core Functionality
- **Student Check-In**: Quick ID-based attendance tracking with real-time student information display
- **Modern Admin Dashboard**: Interactive dashboard with real-time analytics and visual charts
- **User Role Management**: Separate authentication for students and administrators
- **Real-time Notifications**: Flash message system with modern pop-up notifications using Notiflix

### Admin Features
- **Comprehensive Dashboard**:
  - Interactive visitor statistics charts with course-based filtering
  - Real-time attendance data with customizable time ranges (weekly, monthly, yearly, custom)
  - Location-based visitor analytics
  - Recently logged-in students tracking
- **Student Management**: Complete CRUD operations for student records
- **Course Management**: Add, edit, and delete courses with enrollment tracking
- **Profile Management**: Admin profile settings with image upload support
- **Advanced Filtering**: Filter data by time periods, courses, and locations

### Data Management & Export
- **Multiple Export Formats**: CSV and PDF export options with custom date ranges
- **Advanced Analytics**:
  - Attendance by course, age group, and residence
  - Peak hours analysis
  - Monthly/weekly trends
- **Comprehensive Backup System**: Automatic backup of deleted records in both CSV and SQLite formats
- **Location Management**: Hierarchical location system (Province > Municipality > Barangay)

### Security & Authentication
- **Password Reset System**: Email-based password recovery with verification codes
- **Secure Admin Authentication**: Role-based access control
- **Session Management**: Secure session handling with proper logout functionality

### User Experience
- **Responsive Design**: Mobile-friendly interface that works on all devices
- **Modern UI**: Clean, intuitive design with Bootstrap 5
- **Real-time Updates**: Live dashboard updates and notifications
- **Flash Message System**: Consistent notification system across all pages
- **Loading Indicators**: Visual feedback for all operations

## 🏗️ Project Structure

```
Library-Attendance-Management/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── init_db.py                  # Database initialization
├── requirements.txt            # Python dependencies
├── models/                     # Database models
│   ├── __init__.py
│   ├── attendance.py           # Attendance tracking model
│   ├── course.py               # Course management model
│   ├── location.py             # Location hierarchy model
│   ├── student.py              # Student information model
│   └── user.py                 # User authentication model
├── routes/                     # Application routes
│   ├── __init__.py
│   ├── admin_routes.py         # Admin dashboard and management
│   ├── graph_routes.py         # Chart and analytics endpoints
│   └── student_routes.py       # Student check-in functionality
├── templates/                  # HTML templates
│   ├── base.html               # Base template
│   ├── login.html              # Student login page
│   ├── _flash_messages.html    # Flash message component
│   └── admin_new/              # Modern admin interface
│       ├── ae_base.html        # Admin base template
│       ├── ae_dashboard.html   # Interactive dashboard
│       ├── ae_login.html       # Admin login
│       ├── ae_manage.html      # Student management
│       ├── ae_user.html        # Admin profile management
│       ├── ae_forgot_password.html  # Password recovery
│       ├── ae_reset_password.html   # Password reset
│       ├── ae_verify_code.html      # Email verification
│       └── ae_download.html    # Export interface
├── utils/                      # Utility functions
│   ├── backup.py               # Record backup system
│   ├── email_verification.py   # Email verification utilities
│   ├── ensure_dirs.py          # Directory management
│   ├── export.py               # Data export functionality
│   └── graph_export.py         # Chart generation and export
└── static/                     # Static assets
    ├── assets/                 # UI framework assets
    ├── uploads/                # User uploaded files
    └── js/                     # Custom JavaScript
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Git
- (Optional) Docker for containerized deployment

### Local Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/kents00/Library-Attendance.git
    cd Library-Attendance-Management
    ```

2. **Set Up Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Environment Configuration**:
    Create a `.env` file in the root directory:
    ```env
    SECRET_KEY=your-secret-key-here
    DEBUG=True
    DATABASE_URL=sqlite:///instance/attendance.db
    UPLOAD_FOLDER=static/uploads

    # Email Configuration (Optional - for password reset)
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME=your-email@gmail.com
    MAIL_PASSWORD=your-app-password
    ```

5. **Initialize Database**:
    ```bash
    python init_db.py
    ```

6. **Run the Application**:
    ```bash
    python app.py
    ```
    Access the application at [http://localhost:5000](http://localhost:5000)

## 🐳 Docker Deployment

### Quick Start with Docker Hub

```bash
# Pull and run the latest image
docker pull kents00/library-access-monitor:latest
docker run -d -p 5000:5000 --name library-access-monitor kents00/library-access-monitor:latest

# Access the application
# Navigate to http://localhost:5000
```

### Local Docker Build

```bash
# Build and start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Docker Management Commands

```bash
# Stop the container
docker stop library-access-monitor

# Remove the container
docker rm library-access-monitor

# View container logs
docker logs library-access-monitor

# Access container shell
docker exec -it library-access-monitor /bin/bash
```

## 📱 Usage Guide

### For Students
1. **Check-In Process**:
   - Navigate to the main page
   - Enter your student ID
   - View your profile information and confirm attendance
   - Receive confirmation of successful check-in

### For Administrators

#### Initial Setup
1. **First-Time Login**:
   - Default admin credentials are created during database initialization
   - Access admin panel at `/admin/login`
   - Update admin profile and change default password

#### Dashboard Features
1. **Analytics Dashboard**:
   - View real-time visitor statistics with interactive charts
   - Filter data by time periods (weekly, monthly, yearly, custom)
   - Monitor attendance trends by course and location
   - Track recently logged-in students

2. **Student Management**:
   - Add new students with complete profile information
   - Edit existing student records
   - Upload student profile images
   - Manage student-course assignments
   - Bulk operations and search functionality

3. **Course Management**:
   - Create and manage academic courses
   - View enrollment statistics
   - Track course-specific attendance patterns

4. **Data Export & Reports**:
   - Export attendance data in CSV or PDF formats
   - Generate custom reports with date range filtering
   - Download visual charts and analytics
   - Access historical attendance data

5. **System Administration**:
   - Manage admin profiles and permissions
   - Configure system settings
   - Access backup and recovery tools
   - Monitor system health and performance

#### Password Recovery
1. **Forgot Password**:
   - Use the "Forgot Password" link on admin login
   - Enter email address associated with admin account
   - Check email for 6-digit verification code
   - Enter verification code and set new password

## 🔧 Configuration

### Email Setup (Optional)
For password reset functionality, configure email settings in your `.env` file:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use app-specific password for Gmail
```

### File Upload Configuration
```env
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB max file size
```

### Database Configuration
```env
# SQLite (default)
DATABASE_URL=sqlite:///instance/attendance.db

# PostgreSQL (for production)
DATABASE_URL=postgresql://username:password@localhost/dbname

# MySQL
DATABASE_URL=mysql://username:password@localhost/dbname
```

## 🔄 Backup & Recovery

### Automatic Backup Features
- **Deletion Backups**: Automatic backup creation when records are deleted
- **Multiple Formats**: CSV and SQLite backup formats
- **Timestamped Files**: Unique backup files with creation timestamps
- **Organized Storage**: Backups stored in `utils/backups/` directory

### Manual Backup
```bash
# Create manual database backup
python -c "from utils.backup import create_manual_backup; create_manual_backup()"

# Export all data
python -c "from utils.export import export_all_data; export_all_data()"
```

## 🛠️ Development

### Adding New Features
1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Database Changes**:
   - Update model files in `models/`
   - Run database migrations
   - Test changes thoroughly

3. **Frontend Updates**:
   - Modify templates in `templates/`
   - Update static assets in `static/`
   - Ensure responsive design

4. **Backend Logic**:
   - Add routes in appropriate `routes/` files
   - Create utility functions in `utils/`
   - Implement proper error handling

### Testing
```bash
# Run application in debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Test database operations
python -c "from models import db; db.create_all()"
```

## 🚀 Recent Updates

### Version 2.1.0 Features
- ✅ **Modern Admin Interface**: Complete UI overhaul with responsive design
- ✅ **Interactive Dashboard**: Real-time charts and analytics
- ✅ **Flash Message System**: Consistent notifications across all pages
- ✅ **Password Recovery**: Email-based password reset functionality
- ✅ **Course Management**: Complete course CRUD operations
- ✅ **Enhanced Security**: Improved authentication and session management
- ✅ **Location Management**: Hierarchical location system
- ✅ **Advanced Filtering**: Custom date ranges and multi-criteria filtering
- ✅ **Export Improvements**: Enhanced PDF and CSV export capabilities
- ✅ **Backup System**: Comprehensive data backup and recovery

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Commit Changes**: `git commit -m 'Add amazing feature'`
4. **Push to Branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Ensure backward compatibility
- Test across different browsers and devices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/kents00/Library-Attendance/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kents00/Library-Attendance/discussions)

## 📸 Screenshots

### Student Interface
- Clean, intuitive check-in process
- Real-time student information display
- Mobile-responsive design

### Admin Dashboard
- Interactive charts and analytics
- Real-time data visualization
- Comprehensive management tools

### Management Interface
- Modern, professional design
- Efficient data entry forms
- Advanced filtering and search

---

**Made with ❤️ for educational institutions worldwide**
