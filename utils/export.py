from flask import Response, render_template, make_response, current_app
from models import db
from models.attendance import Attendance
from models.student import Student
from models.course import Course
from weasyprint import HTML
import datetime  # Import datetime module
import csv
import io
from datetime import datetime, timedelta, date
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def export_attendance_csv(start_date, end_date, course_id=None):
    """Export attendance data as CSV with unique daily logins"""
    try:
        # Create query for unique daily attendance records
        query = db.session.query(
            Attendance.student_id,
            Student.first_name,
            Student.middle_name,
            Student.last_name,
            Course.course_name,
            db.func.date(Attendance.check_in_time).label('attendance_date'),
            db.func.min(Attendance.check_in_time).label('first_login_time')
        ).join(
            Student, Student.id == Attendance.student_id
        ).join(
            Course, Course.id == Student.course_id
        ).filter(
            Attendance.check_in_time >= start_date,
            Attendance.check_in_time <= end_date
        )

        # Filter by course if specified
        if course_id and course_id.strip():
            query = query.filter(Student.course_id == course_id)

        # Group by student and date to get unique daily logins
        attendance_data = query.group_by(
            Attendance.student_id,
            db.func.date(Attendance.check_in_time)
        ).order_by(
            db.desc('attendance_date'),
            Student.last_name,
            Student.first_name
        ).all()

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            'Student ID',
            'Last Name',
            'First Name',
            'Middle Name',
            'Course',
            'Date',
            'Login Time',
            'Day of Week'
        ]
        writer.writerow(headers)

        # Write attendance data
        for record in attendance_data:
            student_id = record.student_id
            first_name = record.first_name or ''
            middle_name = record.middle_name or ''
            last_name = record.last_name or ''
            course_name = record.course_name or ''

            # Handle attendance_date - convert to date object if it's a string
            attendance_date = record.attendance_date
            if isinstance(attendance_date, str):
                try:
                    attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                except ValueError:
                    current_app.logger.error(f"Error parsing date string: {attendance_date}")
                    continue
            elif not isinstance(attendance_date, date):
                current_app.logger.error(f"Unexpected date type: {type(attendance_date)}")
                continue

            # Handle first_login_time
            login_time = record.first_login_time
            if isinstance(login_time, str):
                try:
                    login_time = datetime.fromisoformat(login_time)
                except ValueError:
                    current_app.logger.error(f"Error parsing login time: {login_time}")
                    continue

            # Format date and time
            date_str = attendance_date.strftime('%Y-%m-%d')
            time_str = login_time.strftime('%I:%M %p')
            day_of_week = attendance_date.strftime('%A')

            writer.writerow([
                student_id,
                last_name,
                first_name,
                middle_name,
                course_name,
                date_str,
                time_str,
                day_of_week
            ])

        # Create response
        csv_content = output.getvalue()
        output.close()

        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_records_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'

        current_app.logger.info(f"CSV export successful: {len(attendance_data)} unique daily records")
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting CSV: {str(e)}")
        raise

def export_attendance_pdf(start_date, end_date, course_id=None):
    """Export attendance data as PDF with unique daily logins"""
    try:
        # Create query for unique daily attendance records (same as CSV)
        query = db.session.query(
            Attendance.student_id,
            Student.first_name,
            Student.middle_name,
            Student.last_name,
            Course.course_name,
            db.func.date(Attendance.check_in_time).label('attendance_date'),
            db.func.min(Attendance.check_in_time).label('first_login_time')
        ).join(
            Student, Student.id == Attendance.student_id
        ).join(
            Course, Course.id == Student.course_id
        ).filter(
            Attendance.check_in_time >= start_date,
            Attendance.check_in_time <= end_date
        )

        # Filter by course if specified
        if course_id and course_id.strip():
            query = query.filter(Student.course_id == course_id)

        # Group by student and date to get unique daily logins
        attendance_data = query.group_by(
            Attendance.student_id,
            db.func.date(Attendance.check_in_time)
        ).order_by(
            db.desc('attendance_date'),
            Student.last_name,
            Student.first_name
        ).all()

        # Create PDF content
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)

        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )

        # Build PDF content
        story = []

        # Title
        title = Paragraph("Library Attendance Records", title_style)
        story.append(title)

        # Date range info
        date_range = Paragraph(
            f"<b>Period:</b> {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}<br/>"
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>"
            f"<b>Total Records:</b> {len(attendance_data)} unique daily logins",
            styles['Normal']
        )
        story.append(date_range)
        story.append(Spacer(1, 20))

        # Create table data
        table_data = [
            ['Student ID', 'Name', 'Course', 'Date', 'Login Time', 'Day']
        ]

        for record in attendance_data:
            full_name = f"{record.last_name}, {record.first_name}"
            if record.middle_name:
                full_name += f" {record.middle_name}"

            # Handle attendance_date - convert to date object if it's a string
            attendance_date = record.attendance_date
            if isinstance(attendance_date, str):
                try:
                    attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                except ValueError:
                    current_app.logger.error(f"Error parsing date string: {attendance_date}")
                    continue
            elif not isinstance(attendance_date, date):
                current_app.logger.error(f"Unexpected date type: {type(attendance_date)}")
                continue

            # Handle first_login_time
            login_time = record.first_login_time
            if isinstance(login_time, str):
                try:
                    login_time = datetime.fromisoformat(login_time)
                except ValueError:
                    current_app.logger.error(f"Error parsing login time: {login_time}")
                    continue

            date_str = attendance_date.strftime('%m/%d/%Y')
            time_str = login_time.strftime('%I:%M %p')
            day_of_week = attendance_date.strftime('%a')

            table_data.append([
                record.student_id,
                full_name,
                record.course_name or 'N/A',
                date_str,
                time_str,
                day_of_week
            ])

        # Create table
        table = Table(table_data, colWidths=[0.8*inch, 2.5*inch, 2*inch, 0.9*inch, 0.9*inch, 0.6*inch])

        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8)
        ]))

        story.append(table)

        # Build PDF
        doc.build(story)

        # Create response
        pdf_content = buffer.getvalue()
        buffer.close()

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_records_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'

        current_app.logger.info(f"PDF export successful: {len(attendance_data)} unique daily records")
        return response

    except Exception as e:
        current_app.logger.error(f"Error exporting PDF: {str(e)}")
        raise

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
