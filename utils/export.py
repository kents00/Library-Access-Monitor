from flask import Response, render_template
from models import db
from models.attendance import Attendance
from models.student import Student
from models.course import Course
from weasyprint import HTML
import datetime  # Import datetime module
import csv
import io

def export_attendance_csv(start_date, end_date=None, course_id=None):
    query = db.session.query(Attendance, Student, Course.course_name).\
        join(Student, Attendance.student_id == Student.id).\
        join(Course, Student.course_id == Course.id).\
        filter(Attendance.check_in_time >= start_date)

    if end_date:
        query = query.filter(Attendance.check_in_time <= end_date)

    if course_id:
        query = query.filter(Course.id == course_id)

    attendance_data = query.all()

    def generate():
        yield "ID,First Name,Last Name,Course,Check-in Time\n"
        for attendance, student, course_name in attendance_data:
            check_in_time_24hr = attendance.check_in_time.strftime("%Y-%m-%d %H:%M:%S")
            yield f"{student.id},{student.first_name},{student.last_name},{course_name},{check_in_time_24hr}\n"

    return Response(generate(),
                   mimetype='text/csv',
                   headers={"Content-Disposition": "attachment;filename=attendance_data.csv"})

def export_attendance_pdf(start_date, end_date=None, course_id=None):
    query = db.session.query(Attendance, Student, Course.course_name).\
        join(Student, Attendance.student_id == Student.id).\
        join(Course, Student.course_id == Course.id).\
        filter(Attendance.check_in_time >= start_date)

    if end_date:
        query = query.filter(Attendance.check_in_time <= end_date)

    if course_id:
        query = query.filter(Course.id == course_id)

    attendance_data = query.all()

    # Create the current date variable
    current_date = datetime.datetime.now()

    rendered_html = render_template("pdf_template.html",
                                   attendance_data=attendance_data,
                                   current_date=current_date)
    pdf = HTML(string=rendered_html).write_pdf()

    return Response(pdf,
                  mimetype='application/pdf',
                  headers={"Content-Disposition": "attachment;filename=attendance_data.pdf"})

def export_model_to_csv(model_data, filename=None):
    """
    Generic function to export any model data to CSV.

    Args:
        model_data: List of model instances or dictionaries
        filename: Optional filename for the CSV

    Returns:
        Response object with CSV data
    """
    if not model_data:
        return Response("No data to export", mimetype='text/plain')

    if not filename:
        filename = f"data_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # Determine columns from the first record
    if hasattr(model_data[0], '__table__'):
        columns = [column.name for column in model_data[0].__table__.columns]
    else:
        columns = model_data[0].keys()

    def generate():
        # Create a StringIO object
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(columns)

        # Yield the header
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Write each row
        for item in model_data:
            if hasattr(item, '__dict__'):
                row = [getattr(item, column) for column in columns]
            else:
                row = [item.get(column) for column in columns]
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return Response(generate(),
                   mimetype='text/csv',
                   headers={"Content-Disposition": f"attachment;filename={filename}"})
