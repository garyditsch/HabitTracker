"""Dashboard service for aggregating data for public dashboard."""

from datetime import datetime, timedelta
from models import get_db
from services.habit_service import get_active_habits
from services.log_service import get_habit_streak, get_completion_stats


def get_public_dashboard_data(days=30):
    """
    Aggregate all data needed for the public dashboard.

    SECURITY CRITICAL: This function MUST only return data for habits
    where is_public = True. Never expose private habits.

    Args:
        days: Number of days of history to include (default: 30)

    Returns:
        Dictionary with:
        {
            'habits': [
                {
                    'id': int,
                    'name': str,
                    'current_streak': int,
                    'completion_rate': float,
                    'logs': [
                        {'date': 'YYYY-MM-DD', 'status': bool},
                        ...
                    ]
                },
                ...
            ],
            'date_range': {
                'start': 'YYYY-MM-DD',
                'end': 'YYYY-MM-DD'
            }
        }
    """
    # SECURITY: Only get public habits (include_private=False)
    public_habits = get_active_habits(include_private=False)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    dashboard_data = {
        'habits': [],
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
    }

    db = get_db()

    for habit in public_habits:
        habit_id = habit['id']

        # Get logs for this habit in the date range
        logs_query = """
            SELECT date, status
            FROM logs
            WHERE habit_id = ?
              AND date >= ?
              AND date <= ?
            ORDER BY date ASC
        """
        logs = db.execute_query(
            logs_query,
            (habit_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )

        # Convert logs to list of dicts
        logs_list = [
            {
                'date': log['date'],
                'status': bool(log['status'])
            }
            for log in logs
        ]

        # Get streak information
        streak_info = get_habit_streak(habit_id)

        # Get completion statistics
        stats = get_completion_stats(habit_id, days)

        habit_data = {
            'id': habit_id,
            'name': habit['name'],
            'current_streak': streak_info['current_streak'],
            'completion_rate': stats['completion_rate'],
            'completed_days': stats['completed_days'],
            'total_days': stats['total_days'],
            'logs': logs_list
        }

        dashboard_data['habits'].append(habit_data)

    return dashboard_data


def get_admin_tracking_data(date):
    """
    Get data for the admin tracking interface for a specific date.

    Args:
        date: Date string in 'YYYY-MM-DD' format or datetime object

    Returns:
        Dictionary with:
        {
            'date': 'YYYY-MM-DD',
            'habits': [
                {
                    'id': int,
                    'name': str,
                    'is_public': bool,
                    'is_logged': bool,
                    'status': bool (if logged)
                },
                ...
            ]
        }
    """
    # Convert datetime to string if needed
    if isinstance(date, datetime):
        date_str = date.strftime('%Y-%m-%d')
    else:
        date_str = date

    # Get all active habits (including private)
    habits = get_active_habits(include_private=True)

    db = get_db()

    # Get existing logs for this date
    logs_query = """
        SELECT habit_id, status
        FROM logs
        WHERE date = ?
    """
    logs = db.execute_query(logs_query, (date_str,))

    # Create a mapping of habit_id to status
    logs_map = {log['habit_id']: bool(log['status']) for log in logs}

    tracking_data = {
        'date': date_str,
        'habits': []
    }

    for habit in habits:
        habit_id = habit['id']
        is_logged = habit_id in logs_map

        habit_data = {
            'id': habit_id,
            'name': habit['name'],
            'is_public': bool(habit['is_public']),
            'order_index': habit['order_index'],
            'is_logged': is_logged,
            'status': logs_map.get(habit_id, False)
        }

        tracking_data['habits'].append(habit_data)

    return tracking_data


def get_habit_history_chart_data(habit_id, days=90):
    """
    Get chart-ready data for a specific habit's history.

    Args:
        habit_id: The habit ID
        days: Number of days to include (default: 90)

    Returns:
        Dictionary with:
        {
            'labels': ['YYYY-MM-DD', ...],  # Dates
            'data': [0, 1, 1, 0, ...],       # Status (0 or 1)
            'dates': ['YYYY-MM-DD', ...]     # Same as labels for reference
        }
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    db = get_db()

    # Get all logs for this habit in the date range
    query = """
        SELECT date, status
        FROM logs
        WHERE habit_id = ?
          AND date >= ?
          AND date <= ?
        ORDER BY date ASC
    """
    logs = db.execute_query(
        query,
        (habit_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )

    # Create a mapping of date to status
    logs_map = {log['date']: int(log['status']) for log in logs}

    # Generate all dates in the range
    labels = []
    data = []
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        labels.append(date_str)
        data.append(logs_map.get(date_str, 0))
        current_date += timedelta(days=1)

    return {
        'labels': labels,
        'data': data,
        'dates': labels  # Redundant but useful for reference
    }
