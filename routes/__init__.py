from flask import Blueprint

#Blueprint for the routes
student_bp = Blueprint('student', __name__)
admin_bp = Blueprint('admin', __name__)

from .admin_routes import admin_bp
from .student_routes import student_bp