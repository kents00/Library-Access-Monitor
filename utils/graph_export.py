import io
import json
import matplotlib.pyplot as plt
from datetime import datetime
from flask import send_file, jsonify, current_app

def generate_visitor_statistics_graph(weekly_course_visits, start_date=None, end_date=None):
    """
    Generate a visitor statistics graph based on the provided data.

    Args:
        weekly_course_visits (dict or str): Course visit data by day of week
        start_date (str, optional): Start date for filtering
        end_date (str, optional): End date for filtering

    Returns:
        Flask response object with the generated image
    """
    try:
        # Parse JSON string if needed
        if isinstance(weekly_course_visits, str):
            try:
                weekly_course_visits = json.loads(weekly_course_visits)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"JSON parsing error: {str(e)}")
                return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))  # Larger figure size
        categories = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        # Add title with date range if provided
        title = 'Weekly Course Visits'
        if start_date and end_date:
            title += f' ({start_date} to {end_date})'

        ax.set_title(title, fontsize=14)

        # Plot the data for each course
        for course, data in weekly_course_visits.items():
            ax.plot(categories, data, marker='o', linewidth=2, label=course)

        # Set labels and grid
        ax.set_xlabel('Day of the Week', fontsize=12)
        ax.set_ylabel('Number of Visitors', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='best', fontsize=10)

        # Enhanced styling
        plt.tight_layout()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Create timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'visitor_statistics_{timestamp}.png'

        # Save to BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=120)
        img.seek(0)
        plt.close(fig)

        # Return file
        return send_file(
            img,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error generating graph: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating graph: {str(e)}'}), 500

def generate_visitor_comparison_graph(monthly_data, title="Monthly Visitor Comparison"):
    """
    Generate a bar chart comparing monthly visitor data.

    Args:
        monthly_data (dict): Monthly visitor data by course
        title (str): Title for the graph

    Returns:
        Flask response object with the generated image
    """
    try:
        fig, ax = plt.subplots(figsize=(12, 7))

        # Extract months and courses
        months = list(range(1, 13))
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        courses = list(monthly_data.keys())

        # Bar position and width
        bar_width = 0.2
        positions = list(range(len(months)))

        # Plot bars for each course, side by side
        for i, course in enumerate(courses):
            course_pos = [p + (i - len(courses)/2 + 0.5) * bar_width for p in positions]
            ax.bar(course_pos, monthly_data[course], width=bar_width, label=course)

        # Set labels and grid
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('Month', fontsize=14)
        ax.set_ylabel('Number of Visitors', fontsize=14)
        ax.set_xticks(positions)
        ax.set_xticklabels(month_names)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend(loc='best', fontsize=12)

        # Enhanced styling
        plt.tight_layout()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Create timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'monthly_comparison_{timestamp}.png'

        # Save to BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=120)
        img.seek(0)
        plt.close(fig)

        # Return file
        return send_file(
            img,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error generating comparison graph: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating graph: {str(e)}'}), 500

def generate_summary_dashboard(weekly_data, monthly_data, top_places=None):
    """
    Generate a summary dashboard with multiple graphs.

    Args:
        weekly_data (dict): Weekly visitor data by course
        monthly_data (dict): Monthly visitor data by course
        top_places (list): Top places data

    Returns:
        Flask response object with the generated image
    """
    try:
        fig = plt.figure(figsize=(16, 10))

        # Create grid for subplots
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        ax1 = fig.add_subplot(gs[0, :])  # Weekly data - top row, full width
        ax2 = fig.add_subplot(gs[1, 0])  # Monthly data - bottom left
        ax3 = fig.add_subplot(gs[1, 1])  # Places - bottom right

        # Plot 1: Weekly data
        categories = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for course, data in weekly_data.items():
            ax1.plot(categories, data, marker='o', linewidth=2, label=course)

        ax1.set_title('Weekly Course Visits', fontsize=14)
        ax1.set_xlabel('Day of Week', fontsize=12)
        ax1.set_ylabel('Number of Visitors', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='upper right', fontsize=10)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # Plot 2: Monthly comparison (simplified)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Get a color for each course
        colors = plt.cm.tab10(range(len(monthly_data)))

        for i, (course, data) in enumerate(monthly_data.items()):
            ax2.plot(month_names, data, marker='s', linewidth=2, label=course, color=colors[i])

        ax2.set_title('Monthly Trends', fontsize=14)
        ax2.set_xlabel('Month', fontsize=12)
        ax2.set_ylabel('Number of Visitors', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.tick_params(axis='x', rotation=45)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # Plot 3: Place visits (if data provided)
        if top_places and len(top_places) > 0:
            places = [p['municipality'] for p in top_places]
            visits = [p['visits'] for p in top_places]

            # Create horizontal bar chart
            bars = ax3.barh(places, visits, color=plt.cm.Paired(range(len(places))))
            ax3.set_title('Top Places of Residence', fontsize=14)
            ax3.set_xlabel('Number of Visits', fontsize=12)
            ax3.invert_yaxis()  # To have the highest value at the top

            # Add value labels to bars
            for bar in bars:
                width = bar.get_width()
                ax3.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width}',
                        ha='left', va='center', fontsize=10)

            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
        else:
            ax3.text(0.5, 0.5, 'No place data available', ha='center', va='center', fontsize=14)
            ax3.axis('off')

        # Set a title for the entire figure
        fig.suptitle('Library Attendance Dashboard', fontsize=18, y=0.98)

        # Create timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dashboard_summary_{timestamp}.png'

        # Save to BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=120)
        img.seek(0)
        plt.close(fig)

        # Return file
        return send_file(
            img,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error generating summary dashboard: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating dashboard: {str(e)}'}), 500
