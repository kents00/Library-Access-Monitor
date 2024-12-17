# Library Attendance System

A web-based library attendance system built with Flask, designed to streamline student attendance management in libraries. This application allows students to check in via ID, and it provides admins with tools to view attendance metrics, generate reports, and manage user data.

![Screenshot 2024-10-25 213446](https://github.com/user-attachments/assets/84d7a246-d6a4-4a39-b164-31001f46e6e2)

## Features

- **Student Check-In**: Students can log in using their ID for attendance tracking.
- **Admin Dashboard**: An interactive dashboard for library staff to view daily attendance counts, peak hours, and other useful metrics.
- **User Roles**: Separate roles for regular users (students) and admin users.
- **Data Export**: Attendance data export options in CSV and PDF formats.
- **Backup System**: Integrated backup mechanism for SQLite database.
- **Analytics**: View attendance by course, age group, and residence.

## Project Structure

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, Flask, SQLite
- **Models**:
    - **Student**: Stores details like ID, name, course, age, and place of residence.
    - **Attendance**: Tracks check-in times with student IDs.
    - **User**: Stores user credentials, including roles.

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
    flask db init
    flask db migrate
    flask db upgrade
    ```
    
5. **Run the Application**:
    
    ```bash
    flask run or  python app.py
    ```
    
    Access the app at [http://localhost:5000](http://localhost:5000/).
    

## Usage

1. **Student Check-In**: Enter student ID to check in, displaying student information like name, course, and picture.
2. **Admin Dashboard**:
    - View attendance analytics filtered by week, month, or year.
    - Download reports in CSV or PDF formats.
    - Manage students: Add or remove students from the system.

## Database Backup

- A built-in backup mechanism supports secure backup and restoration of the SQLite database.

## Contributions

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
