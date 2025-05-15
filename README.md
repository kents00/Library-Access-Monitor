# Library Access Monitor

A web-based library attendance system built with Flask, designed to streamline student attendance management in libraries. This application allows students to check in via ID, and it provides admins with tools to view attendance metrics, generate reports, and manage user data.

![image](https://github.com/user-attachments/assets/ad83c896-f126-48bb-b4ce-c71e4e6d13ba)

## Features

- **Student Check-In**: Students can log in using their ID for attendance tracking.
- **Admin Dashboard**: An interactive dashboard for library staff to view daily attendance counts, peak hours, and other useful metrics.
- **User Roles**: Separate roles for regular users (students) and admin users.
- **Data Export**: Attendance data export options in CSV and PDF formats.
- **Comprehensive Backup System**: Automatic backup of deleted records in both CSV and SQLite formats.
- **Analytics**: View attendance by course, age group, and residence.

## Project Structure

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, Flask, SQLite
- **Models**:
    - **Student**: Stores details like ID, name, course, age, and place of residence.
    - **Attendance**: Tracks check-in times with student IDs.
    - **User**: Stores user credentials, including roles.
- **Utils**:
    - **backup.py**: Handles automatic backup of deleted records
    - **export.py**: Manages data export functionality
    - **ensure_dirs.py**: Ensures all required directories exist

## Installation

1. **Clone the Repository**:

    ```bash
    git clone <https://github.com/kents00/Library-Attendance.git>
    cd Library-Attendance
    ```

2. **Set Up Virtual Environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\\Scripts\\activate`
    ```

3. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Database**:
Run the following commands to initialize the SQLite database and apply migrations.

    ```bash
    python init_db.py
    ```

5. **Run the Application**:

    ```bash
    flask run
    ```

    Access the app at [http://localhost:5000](http://localhost:5000/).


## Usage

1. **Student Check-In**: Enter student ID to check in, displaying student information like name, course, and picture.
2. **Admin Dashboard**:
    - View attendance analytics filtered by week, month, or year.
    - Download reports in CSV or PDF formats.
    - Manage students: Add or remove students from the system.

## Database Backup

The system includes a robust backup mechanism with the following features:
- **Automatic Backups**: When records are deleted, the system automatically creates backups.
- **Dual-Format Backup**: Each backup is stored in both CSV and SQLite formats for flexibility.
- **Timestamped Files**: Backup files include timestamps to differentiate between backup operations.
- **Backup Location**: All backups are stored in the `utils/backups` directory.

## Docker Deployment

### Docker Hub

The easiest way to deploy the application is using Docker Hub:

```bash
# Pull the image from Docker Hub
docker pull kents00/library-access-monitor:latest

# Run the container
docker run -d -p 5000:5000 --name library-access-monitor kents00/library-access-monitor:latest

# Stop the container
docker stop library-access-monitor

# Remove the container
docker rm library-access-monitor
```

### Local Docker Build

Alternatively, you can build and run using the project's Docker files:

```bash
# Build and start the container
docker-compose up -d

# To stop the container
docker-compose down
```

## Contributions

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
