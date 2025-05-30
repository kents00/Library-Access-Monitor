from flask import Blueprint, request, current_app, jsonify
import json
from utils.graph_export import (
    generate_visitor_statistics_graph,
    generate_visitor_comparison_graph,
    generate_summary_dashboard
)
from datetime import datetime

# Create a Blueprint for graph routes
graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/download_graph', methods=['GET', 'POST'])
def download_graph():
    """
    Handle graph downloads with different time ranges
    """
    try:
        # Process either GET or POST parameters
        if request.method == 'POST':
            weekly_course_visits_str = request.form.get('weekly_course_visits')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            graph_type = request.form.get('type', 'weekly')
        else:  # GET
            weekly_course_visits_str = request.args.get('weekly_course_visits')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            graph_type = request.args.get('type', 'weekly')

        if not weekly_course_visits_str:
            current_app.logger.error("Missing weekly_course_visits parameter")
            return jsonify({'success': False, 'message': 'Missing data parameter'}), 400

        # Generate the appropriate graph based on type
        if graph_type == 'summary':
            # For summary dashboard, we need monthly data too
            try:
                monthly_data = request.args.get('monthly_data') or request.form.get('monthly_data')
                top_places = request.args.get('top_places') or request.form.get('top_places')

                if monthly_data:
                    monthly_data = json.loads(monthly_data)
                else:
                    # Use weekly data for both if monthly not provided
                    monthly_data = json.loads(weekly_course_visits_str)

                if top_places:
                    top_places = json.loads(top_places)

                return generate_summary_dashboard(
                    json.loads(weekly_course_visits_str),
                    monthly_data,
                    top_places
                )
            except Exception as e:
                current_app.logger.error(f"Error generating summary: {str(e)}")
                # Fall back to weekly view
                return generate_visitor_statistics_graph(weekly_course_visits_str, start_date, end_date)

        elif graph_type == 'monthly':
            # Generate monthly comparison graph
            return generate_visitor_comparison_graph(
                json.loads(weekly_course_visits_str),
                title=f"Monthly Visitor Comparison ({start_date} to {end_date})" if start_date and end_date else "Monthly Visitor Comparison"
            )

        else:  # Default to weekly
            # Generate weekly visitor statistics graph
            return generate_visitor_statistics_graph(weekly_course_visits_str, start_date, end_date)

    except Exception as e:
        current_app.logger.error(f"Error in download_graph: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error generating graph: {str(e)}'}), 500
