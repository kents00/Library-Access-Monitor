from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models for proper table creation sequence
# Don't try to import models that depend on db here as that would create circular imports
from .location import Location
from .user import User
from .course import Course
from .student import Student
from .attendance import Attendance