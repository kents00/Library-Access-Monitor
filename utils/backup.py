import os
import csv
import datetime
import sqlite3
import json
from models import db
from models.student import Student
from models.attendance import Attendance
from models.course import Course
from models.location import Location
from sqlalchemy.inspection import inspect

def create_backup_directory():
    """Create a backup directory if it doesn't exist."""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def backup_deleted_records(model_name, records):
    """
    Create a CSV backup of deleted database records.

    Args:
        model_name (str): The name of the model being backed up (Student, Attendance, etc.)
        records (list): The list of records to backup

    Returns:
        str: Path to the created backup file
    """
    if not records:
        return None

    # Create timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = create_backup_directory()

    # Create filename with timestamp
    backup_file = os.path.join(backup_dir, f"{model_name}_deleted_{timestamp}.csv")

    # Get column names from the first record
    if hasattr(records[0], '__table__'):
        columns = [column.name for column in records[0].__table__.columns]
    else:
        # If the record is a dictionary
        columns = records[0].keys()

    with open(backup_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(columns)

        # Write data rows
        for record in records:
            if hasattr(record, '__dict__'):
                # If record is a SQLAlchemy model instance
                row = [getattr(record, column) for column in columns]
            else:
                # If record is a dictionary
                row = [record.get(column) for column in columns]
            writer.writerow(row)

    # Also create a SQLite backup
    sqlite_backup_path = backup_sqlite_records(model_name, records, timestamp)

    print(f"Backups created: CSV: {backup_file}, SQLite: {sqlite_backup_path}")
    return backup_file

def backup_sqlite_records(model_name, records, timestamp=None):
    """
    Create an SQLite database backup of deleted records.

    Args:
        model_name (str): Name of the model being backed up
        records (list): List of records to backup
        timestamp (str): Optional timestamp to use for filename

    Returns:
        str: Path to the SQLite backup file
    """
    if not records:
        return None

    # Create timestamp if not provided
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir = create_backup_directory()
    sqlite_file = os.path.join(backup_dir, f"{model_name}_deleted_{timestamp}.db")

    # Connect to the new SQLite database
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()

    # Get table schema information from the model
    if hasattr(records[0], '__table__'):
        # Create a table with the same schema as the original
        model_class = records[0].__class__
        table_name = model_class.__tablename__

        # Get column definitions
        columns = []
        primary_key = None

        for column in inspect(model_class).columns:
            col_type = str(column.type)
            nullable = "" if column.nullable else "NOT NULL"
            if column.primary_key:
                primary_key = column.name
                pk_def = "PRIMARY KEY"
            else:
                pk_def = ""

            columns.append(f"{column.name} {col_type} {nullable} {pk_def}".strip())

        # Create table
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        cursor.execute(create_table_sql)

        # Insert data
        for record in records:
            data = {}
            for column in inspect(model_class).columns:
                value = getattr(record, column.name)
                # Convert Python objects to JSON strings if needed
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                data[column.name] = value

            placeholders = ', '.join(['?' for _ in data])
            columns_str = ', '.join(data.keys())
            cursor.execute(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                list(data.values())
            )
    else:
        # Handle dictionary records
        table_name = model_name.lower()

        # Create table based on dictionary keys
        columns = records[0].keys()
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{col} TEXT' for col in columns])})"
        cursor.execute(create_table_sql)

        # Insert data
        for record in records:
            placeholders = ', '.join(['?' for _ in record])
            columns_str = ', '.join(record.keys())
            cursor.execute(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                list(record.values())
            )

    conn.commit()
    conn.close()

    print(f"SQLite backup created: {sqlite_file}")
    return sqlite_file
