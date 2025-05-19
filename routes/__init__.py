from flask import Blueprint

#Blueprint for the routes
student_bp = Blueprint('student', __name__)
admin_bp = Blueprint('admin', __name__)
graph_bp = Blueprint('graph', __name__)

from .admin_routes import admin_bp
from .student_routes import student_bp
from .graph_routes import graph_bp