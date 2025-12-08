"""Admin routes for habit tracking and management."""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.decorators import login_required
from services import (
    get_admin_tracking_data,
    save_day_logs,
    get_all_habits,
    get_habit_by_id,
    create_habit,
    update_habit,
    reorder_habits,
    delete_habit,
    invalidate_dashboard_cache
)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/track')
@login_required
def track():
    """
    Daily habit tracking interface.

    Query parameters:
        date: Optional date in YYYY-MM-DD format (defaults to today)
    """
    # Get date from query parameter or default to today
    date_str = request.args.get('date')

    if date_str:
        try:
            # Validate date format
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Using today instead.', 'error')
            date = datetime.now().date()
    else:
        date = datetime.now().date()

    return render_template('admin/track.html', date=date.strftime('%Y-%m-%d'))


@admin_bp.route('/api/track/data')
@login_required
def track_data():
    """
    API endpoint to get tracking data for a specific date.

    Query parameters:
        date: Date in YYYY-MM-DD format (required)

    Returns:
        JSON with habits and their log status for the date
    """
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400

    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get tracking data
    data = get_admin_tracking_data(date_str)

    return jsonify(data)


@admin_bp.route('/api/track/save', methods=['POST'])
@login_required
def save_tracking():
    """
    API endpoint to save habit logs for a day.

    SECURITY: Protected by @login_required decorator.

    Request body:
        {
            "date": "YYYY-MM-DD",
            "logs": [
                {"habit_id": 1, "status": true, "value": 10},
                {"habit_id": 2, "status": false}
            ]
        }

    Returns:
        JSON with success status
    """
    data = request.get_json()

    if not data or 'date' not in data or 'logs' not in data:
        return jsonify({'error': 'Invalid request data'}), 400

    date_str = data['date']
    logs = data['logs']

    # Validate date format
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Convert logs list to dict for save_day_logs
    habit_statuses = {}
    for log in logs:
        habit_id = log['habit_id']
        # Check if value is provided
        if 'value' in log and log['value'] is not None:
            habit_statuses[habit_id] = {
                'status': log['status'],
                'value': log['value']
            }
        else:
            habit_statuses[habit_id] = log['status']

    # Save logs
    count = save_day_logs(date_str, habit_statuses)

    # Invalidate dashboard cache since data changed
    invalidate_dashboard_cache()

    return jsonify({
        'success': True,
        'message': f'Saved {count} logs for {date_str}'
    })


@admin_bp.route('/settings')
@login_required
def settings():
    """Habit management interface."""
    return render_template('admin/settings.html')


@admin_bp.route('/api/habits')
@login_required
def get_habits():
    """
    API endpoint to get all habits (including private).

    Returns:
        JSON with all habits
    """
    habits = get_all_habits(include_private=True)

    # Convert to list of dicts
    habits_list = [
        {
            'id': h['id'],
            'name': h['name'],
            'is_active': bool(h['is_active']),
            'is_public': bool(h['is_public']),
            'order_index': h['order_index'],
            'tracks_value': bool(h['tracks_value']) if 'tracks_value' in h.keys() else False,
            'value_unit': h['value_unit'] if 'value_unit' in h.keys() else None,
            'created_at': h['created_at']
        }
        for h in habits
    ]

    return jsonify({'habits': habits_list})


@admin_bp.route('/api/habits', methods=['POST'])
@login_required
def create_new_habit():
    """
    API endpoint to create a new habit.

    Request body:
        {
            "name": "Habit name",
            "is_public": true,
            "tracks_value": false,
            "value_unit": "pushups"
        }

    Returns:
        JSON with created habit ID
    """
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Habit name required'}), 400

    name = data['name'].strip()

    if not name or len(name) > 100:
        return jsonify({'error': 'Habit name must be 1-100 characters'}), 400

    is_public = data.get('is_public', True)
    tracks_value = data.get('tracks_value', False)
    value_unit = data.get('value_unit')
    value_aggregation_type = data.get('value_aggregation_type', 'absolute')

    # Validate value_unit if provided
    if value_unit and len(value_unit) > 50:
        return jsonify({'error': 'Value unit must be 50 characters or less'}), 400

    # Validate value_aggregation_type
    if value_aggregation_type not in ['absolute', 'cumulative']:
        return jsonify({'error': 'Value aggregation type must be "absolute" or "cumulative"'}), 400

    # Create habit
    habit_id = create_habit(
        name,
        is_public=is_public,
        tracks_value=tracks_value,
        value_unit=value_unit,
        value_aggregation_type=value_aggregation_type
    )

    # Invalidate dashboard cache
    invalidate_dashboard_cache()

    return jsonify({
        'success': True,
        'habit_id': habit_id,
        'message': 'Habit created successfully'
    }), 201


@admin_bp.route('/api/habits/<int:habit_id>', methods=['PUT'])
@login_required
def update_existing_habit(habit_id):
    """
    API endpoint to update a habit.

    Request body:
        {
            "name": "New name",
            "is_active": true,
            "is_public": false,
            "tracks_value": true,
            "value_unit": "lbs"
        }

    Returns:
        JSON with success status
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate habit exists
    habit = get_habit_by_id(habit_id)
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404

    # Build update dict
    updates = {}

    if 'name' in data:
        name = data['name'].strip()
        if not name or len(name) > 100:
            return jsonify({'error': 'Habit name must be 1-100 characters'}), 400
        updates['name'] = name

    if 'is_active' in data:
        updates['is_active'] = bool(data['is_active'])

    if 'is_public' in data:
        updates['is_public'] = bool(data['is_public'])

    if 'tracks_value' in data:
        updates['tracks_value'] = bool(data['tracks_value'])

    if 'value_unit' in data:
        value_unit = data['value_unit']
        # Allow None/null to clear the value_unit
        if value_unit is not None and len(value_unit) > 50:
            return jsonify({'error': 'Value unit must be 50 characters or less'}), 400
        updates['value_unit'] = value_unit

    if 'value_aggregation_type' in data:
        value_aggregation_type = data['value_aggregation_type']
        if value_aggregation_type not in ['absolute', 'cumulative']:
            return jsonify({'error': 'Value aggregation type must be "absolute" or "cumulative"'}), 400
        updates['value_aggregation_type'] = value_aggregation_type

    # Update habit
    update_habit(habit_id, **updates)

    # Invalidate dashboard cache
    invalidate_dashboard_cache()

    return jsonify({
        'success': True,
        'message': 'Habit updated successfully'
    })


@admin_bp.route('/api/habits/<int:habit_id>', methods=['DELETE'])
@login_required
def delete_existing_habit(habit_id):
    """
    API endpoint to delete (deactivate) a habit.

    Returns:
        JSON with success status
    """
    # Validate habit exists
    habit = get_habit_by_id(habit_id)
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404

    # Soft delete
    delete_habit(habit_id)

    # Invalidate dashboard cache
    invalidate_dashboard_cache()

    return jsonify({
        'success': True,
        'message': 'Habit deleted successfully'
    })


@admin_bp.route('/api/habits/reorder', methods=['POST'])
@login_required
def reorder_habits_endpoint():
    """
    API endpoint to reorder habits.

    Request body:
        {
            "habit_ids": [3, 1, 2]  // New order
        }

    Returns:
        JSON with success status
    """
    data = request.get_json()

    if not data or 'habit_ids' not in data:
        return jsonify({'error': 'habit_ids array required'}), 400

    habit_ids = data['habit_ids']

    if not isinstance(habit_ids, list):
        return jsonify({'error': 'habit_ids must be an array'}), 400

    # Reorder habits
    count = reorder_habits(habit_ids)

    # Invalidate dashboard cache (order affects display)
    invalidate_dashboard_cache()

    return jsonify({
        'success': True,
        'message': f'Reordered {count} habits'
    })
