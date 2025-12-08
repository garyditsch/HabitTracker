"""Dashboard service for aggregating data for public dashboard."""

from datetime import datetime, timedelta
from calendar import monthrange
from models import get_db
from services.habit_service import get_active_habits
from services.log_service import get_habit_streak, get_completion_stats, get_value_stats


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
            SELECT date, status, value
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
                'status': bool(log['status']),
                'value': log['value']
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
            'created_at': habit['created_at'],
            'tracks_value': bool(habit['tracks_value']) if 'tracks_value' in habit.keys() else False,
            'value_unit': habit['value_unit'] if 'value_unit' in habit.keys() else None,
            'value_aggregation_type': habit['value_aggregation_type'] if 'value_aggregation_type' in habit.keys() else 'absolute',
            'current_streak': streak_info['current_streak'],
            'completion_rate': stats['completion_rate'],
            'completed_days': stats['completed_days'],
            'total_days': stats['total_days'],
            'logs': logs_list
        }

        # Add value statistics if the habit tracks values
        if 'tracks_value' in habit.keys() and habit['tracks_value']:
            value_stats = get_value_stats(habit_id, days)
            habit_data['value_stats'] = value_stats

            # Add aggregated statistics for cumulative habits
            aggregation_type = habit['value_aggregation_type'] if 'value_aggregation_type' in habit.keys() else 'absolute'
            if aggregation_type == 'cumulative':
                habit_data['value_aggregations'] = {
                    'week': get_cumulative_total(habit_id, 7),
                    'month': get_cumulative_total(habit_id, 30),
                    'year': get_cumulative_total(habit_id, 365)
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
        SELECT habit_id, status, value
        FROM logs
        WHERE date = ?
    """
    logs = db.execute_query(logs_query, (date_str,))

    # Create a mapping of habit_id to status and value
    logs_map = {
        log['habit_id']: {
            'status': bool(log['status']),
            'value': log['value']
        }
        for log in logs
    }

    tracking_data = {
        'date': date_str,
        'habits': []
    }

    for habit in habits:
        habit_id = habit['id']
        is_logged = habit_id in logs_map
        log_data = logs_map.get(habit_id, {'status': False, 'value': None})

        habit_data = {
            'id': habit_id,
            'name': habit['name'],
            'is_public': bool(habit['is_public']),
            'order_index': habit['order_index'],
            'tracks_value': bool(habit['tracks_value']) if 'tracks_value' in habit.keys() else False,
            'value_unit': habit['value_unit'] if 'value_unit' in habit.keys() else None,
            'value_aggregation_type': habit['value_aggregation_type'] if 'value_aggregation_type' in habit.keys() else 'absolute',
            'is_logged': is_logged,
            'status': log_data['status'],
            'value': log_data['value']
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
        SELECT date, status, value
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

    # Create a mapping of date to status and value
    logs_map = {log['date']: {'status': int(log['status']), 'value': log['value']} for log in logs}

    # Generate all dates in the range
    labels = []
    data = []
    current_date = start_date

    values = []
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        labels.append(date_str)
        log_entry = logs_map.get(date_str, {'status': 0, 'value': None})
        data.append(log_entry['status'])
        values.append(log_entry['value'])
        current_date += timedelta(days=1)

    return {
        'labels': labels,
        'data': data,
        'values': values,  # Value data for value-tracking habits
        'dates': labels  # Redundant but useful for reference
    }


def get_yearly_heatmap_data(year=None):
    """
    Get yearly heatmap data showing combined daily completion percentages.

    SECURITY CRITICAL: This function MUST only return data for habits
    where is_public = True. Never expose private habits.

    IMPORTANT: Percentages are calculated based on habits that existed on each date
    (using created_at timestamp), not the current list of habits. This ensures
    historical accuracy when habits are added or removed.

    Args:
        year: Year as integer (default: current year)

    Returns:
        Dictionary with:
        {
            'year': int,
            'is_leap_year': bool,
            'months': [
                {
                    'month': int (1-12),
                    'month_name': str,
                    'first_day_weekday': int (0=Monday, 6=Sunday),
                    'days': [
                        {
                            'date': 'YYYY-MM-DD',
                            'day_of_month': int,
                            'completion_percentage': float,
                            'completed_count': int,
                            'total_count': int (habits that existed on this date)
                        },
                        ...
                    ]
                },
                ...
            ],
            'overall_stats': {
                'total_days_tracked': int,
                'average_completion': float,
                'best_day': {
                    'date': 'YYYY-MM-DD',
                    'percentage': float
                },
                'worst_day': {
                    'date': 'YYYY-MM-DD',
                    'percentage': float
                }
            }
        }
    """
    # Default to current year
    if year is None:
        year = datetime.now().year

    # Date range for the year
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()

    db = get_db()

    # SECURITY: Get ALL public habits (including deleted) that existed during this year
    # We need to include deleted habits to get accurate historical data
    habits_query = """
        SELECT id, name, created_at
        FROM habits
        WHERE is_public = 1
          AND created_at <= ?
        ORDER BY created_at ASC
    """

    # Get all public habits created on or before the end of the year
    all_habits = db.execute_query(
        habits_query,
        (end_date.strftime('%Y-%m-%d 23:59:59'),)
    )

    # If no public habits, return empty structure
    if not all_habits:
        return {
            'year': year,
            'is_leap_year': (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0),
            'months': [],
            'overall_stats': {
                'total_days_tracked': 0,
                'average_completion': 0.0,
                'best_day': None,
                'worst_day': None
            }
        }

    # Get all habit IDs for this year
    habit_ids = [habit['id'] for habit in all_habits]

    # Get all completed logs for these habits in this year
    placeholders = ','.join('?' * len(habit_ids))
    logs_query = f"""
        SELECT l.habit_id, l.date
        FROM logs l
        WHERE l.habit_id IN ({placeholders})
          AND l.status = 1
          AND l.date >= ?
          AND l.date <= ?
    """

    params = tuple(habit_ids) + (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    logs = db.execute_query(logs_query, params)

    # Create a mapping of date -> set of completed habit_ids
    completed_by_date = {}
    for log in logs:
        date_str = log['date']
        if date_str not in completed_by_date:
            completed_by_date[date_str] = set()
        completed_by_date[date_str].add(log['habit_id'])

    # Get the first log date for each habit (this is when the habit "started" for historical purposes)
    # Use first log date instead of created_at to handle backdated logs correctly
    first_log_query = f"""
        SELECT habit_id, MIN(date) as first_log_date
        FROM logs
        WHERE habit_id IN ({placeholders})
        GROUP BY habit_id
    """
    first_logs = db.execute_query(first_log_query, tuple(habit_ids))
    first_log_map = {log['habit_id']: log['first_log_date'] for log in first_logs}

    # Create a mapping of habit_id -> effective start date
    # Use first log date if available, otherwise fall back to created_at date
    habit_created_dates = {}
    for habit in all_habits:
        habit_id = habit['id']
        if habit_id in first_log_map:
            # Use first log date
            habit_created_dates[habit_id] = first_log_map[habit_id]
        else:
            # No logs yet, use created_at timestamp
            created_str = habit['created_at'].split(' ')[0]  # Get just the date part
            habit_created_dates[habit_id] = created_str

    # Build months structure
    months_data = []
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Track statistics
    all_days_data = []

    for month_num in range(1, 13):
        # Get number of days in this month
        _, num_days = monthrange(year, month_num)

        # Get first day of month (0=Monday, 6=Sunday)
        first_day = datetime(year, month_num, 1).weekday()

        days_data = []

        for day_num in range(1, num_days + 1):
            date_obj = datetime(year, month_num, day_num).date()
            date_str = date_obj.strftime('%Y-%m-%d')

            # Count habits that existed on this date (created_at <= date)
            habits_on_date = [
                habit_id for habit_id, created_date in habit_created_dates.items()
                if created_date <= date_str
            ]
            total_habits_on_date = len(habits_on_date)

            # For dates where no habits existed yet or future dates, show 0% (gray box)
            if total_habits_on_date == 0:
                completion_percentage = 0.0
                completed_count = 0
            else:
                # Count completions for habits that existed on this date
                completed_on_date = completed_by_date.get(date_str, set())
                completed_count = len([
                    habit_id for habit_id in completed_on_date
                    if habit_id in habits_on_date
                ])

                # Calculate percentage based on habits that existed on this date
                completion_percentage = (completed_count / total_habits_on_date) * 100.0

            day_data = {
                'date': date_str,
                'day_of_month': day_num,
                'completion_percentage': round(completion_percentage, 1),
                'completed_count': completed_count,
                'total_count': total_habits_on_date
            }

            days_data.append(day_data)

            # Only include in overall stats if habits existed (for accurate statistics)
            if total_habits_on_date > 0:
                all_days_data.append(day_data)

        month_data = {
            'month': month_num,
            'month_name': month_names[month_num - 1],
            'first_day_weekday': first_day,
            'days': days_data
        }

        months_data.append(month_data)

    # Calculate overall statistics
    total_days_tracked = len(all_days_data)

    if total_days_tracked > 0:
        average_completion = sum(day['completion_percentage'] for day in all_days_data) / total_days_tracked

        # Find best and worst days
        best_day = max(all_days_data, key=lambda d: d['completion_percentage'])
        worst_day = min(all_days_data, key=lambda d: d['completion_percentage'])

        overall_stats = {
            'total_days_tracked': total_days_tracked,
            'average_completion': round(average_completion, 1),
            'best_day': {
                'date': best_day['date'],
                'percentage': best_day['completion_percentage']
            },
            'worst_day': {
                'date': worst_day['date'],
                'percentage': worst_day['completion_percentage']
            }
        }
    else:
        overall_stats = {
            'total_days_tracked': 0,
            'average_completion': 0.0,
            'best_day': None,
            'worst_day': None
        }

    return {
        'year': year,
        'is_leap_year': (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0),
        'months': months_data,
        'overall_stats': overall_stats
    }


def get_cumulative_total(habit_id, days):
    """
    Calculate the cumulative total of values for a habit over a time period.

    Args:
        habit_id: The habit ID
        days: Number of days to sum (7 for week, 30 for month, 365 for year)

    Returns:
        Float: Total sum of values, or 0 if no values recorded
    """
    from datetime import datetime, timedelta

    db = get_db()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    query = """
        SELECT COALESCE(SUM(value), 0) as total
        FROM logs
        WHERE habit_id = ?
          AND date >= ?
          AND date <= ?
          AND value IS NOT NULL
    """

    result = db.execute_query(
        query,
        (habit_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )

    return float(result[0]['total']) if result else 0.0


def get_archived_habits_data():
    """
    Get all archived (inactive) public habits with their lifetime statistics.

    SECURITY CRITICAL: This function MUST only return data for habits
    where is_public = True. Never expose private habits.

    Returns:
        List of archived habits with:
        [
            {
                'id': int,
                'name': str,
                'created_at': str,
                'total_completions': int,
                'total_days_tracked': int,
                'completion_rate': float,
                'longest_streak': int,
                'date_range': {
                    'first_log': 'YYYY-MM-DD',
                    'last_log': 'YYYY-MM-DD'
                }
            },
            ...
        ]
    """
    db = get_db()

    # SECURITY: Only get archived public habits (is_active=0, is_public=1)
    archived_query = """
        SELECT id, name, created_at
        FROM habits
        WHERE is_active = 0
          AND is_public = 1
        ORDER BY created_at DESC
    """

    archived_habits = db.execute_query(archived_query)

    if not archived_habits:
        return []

    archived_data = []

    for habit in archived_habits:
        habit_id = habit['id']

        # Get all logs for this habit
        logs_query = """
            SELECT date, status
            FROM logs
            WHERE habit_id = ?
            ORDER BY date ASC
        """
        logs = db.execute_query(logs_query, (habit_id,))

        if not logs:
            # Habit has no logs, skip it
            continue

        # Calculate statistics
        total_logs = len(logs)
        completed_logs = [log for log in logs if log['status']]
        total_completions = len(completed_logs)
        completion_rate = (total_completions / total_logs * 100.0) if total_logs > 0 else 0.0

        # Get date range
        first_log = logs[0]['date']
        last_log = logs[-1]['date']

        # Calculate longest streak
        longest_streak = 0
        current_streak = 0
        prev_date = None

        for log in logs:
            if log['status']:
                # Completed
                if prev_date is None:
                    current_streak = 1
                else:
                    # Check if consecutive days
                    log_date = datetime.strptime(log['date'], '%Y-%m-%d').date()
                    prev_date_obj = datetime.strptime(prev_date, '%Y-%m-%d').date()
                    days_diff = (log_date - prev_date_obj).days

                    if days_diff == 1:
                        current_streak += 1
                    else:
                        current_streak = 1

                longest_streak = max(longest_streak, current_streak)
                prev_date = log['date']
            else:
                # Not completed, reset streak
                current_streak = 0
                prev_date = log['date']

        habit_data = {
            'id': habit_id,
            'name': habit['name'],
            'created_at': habit['created_at'],
            'total_completions': total_completions,
            'total_days_tracked': total_logs,
            'completion_rate': round(completion_rate, 1),
            'longest_streak': longest_streak,
            'date_range': {
                'first_log': first_log,
                'last_log': last_log
            }
        }

        archived_data.append(habit_data)

    return archived_data
