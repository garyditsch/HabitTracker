"""Log service for habit tracking operations."""

from datetime import datetime, timedelta
from models import get_db


def get_logs_for_date(date, include_private=True):
    """
    Get all logs for a specific date.

    Args:
        date: Date string in 'YYYY-MM-DD' format or datetime object
        include_private: If True, includes logs for private habits

    Returns:
        List of log rows with habit information
    """
    db = get_db()

    # Convert datetime to string if needed
    if isinstance(date, datetime):
        date = date.strftime('%Y-%m-%d')

    if include_private:
        query = """
            SELECT l.id, l.habit_id, l.date, l.status,
                   h.name as habit_name, h.is_public, h.order_index
            FROM logs l
            JOIN habits h ON l.habit_id = h.id
            WHERE l.date = ?
            ORDER BY h.order_index ASC, h.created_at ASC
        """
    else:
        query = """
            SELECT l.id, l.habit_id, l.date, l.status,
                   h.name as habit_name, h.is_public, h.order_index
            FROM logs l
            JOIN habits h ON l.habit_id = h.id
            WHERE l.date = ? AND h.is_public = 1
            ORDER BY h.order_index ASC, h.created_at ASC
        """

    return db.execute_query(query, (date,))


def get_logs_for_habit(habit_id, start_date=None, end_date=None):
    """
    Get logs for a specific habit within a date range.

    Args:
        habit_id: The habit ID
        start_date: Optional start date (YYYY-MM-DD or datetime)
        end_date: Optional end date (YYYY-MM-DD or datetime)

    Returns:
        List of log rows ordered by date descending
    """
    db = get_db()

    # Convert datetime to string if needed
    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, datetime):
        end_date = end_date.strftime('%Y-%m-%d')

    if start_date and end_date:
        query = """
            SELECT id, habit_id, date, status
            FROM logs
            WHERE habit_id = ? AND date >= ? AND date <= ?
            ORDER BY date DESC
        """
        return db.execute_query(query, (habit_id, start_date, end_date))
    elif start_date:
        query = """
            SELECT id, habit_id, date, status
            FROM logs
            WHERE habit_id = ? AND date >= ?
            ORDER BY date DESC
        """
        return db.execute_query(query, (habit_id, start_date))
    elif end_date:
        query = """
            SELECT id, habit_id, date, status
            FROM logs
            WHERE habit_id = ? AND date <= ?
            ORDER BY date DESC
        """
        return db.execute_query(query, (habit_id, end_date))
    else:
        query = """
            SELECT id, habit_id, date, status
            FROM logs
            WHERE habit_id = ?
            ORDER BY date DESC
        """
        return db.execute_query(query, (habit_id,))


def upsert_log(habit_id, date, status):
    """
    Insert or update a log entry for a habit on a specific date.

    Args:
        habit_id: The habit ID
        date: Date string in 'YYYY-MM-DD' format or datetime object
        status: Boolean indicating completion (True) or not (False)

    Returns:
        ID of inserted/updated log
    """
    db = get_db()

    # Convert datetime to string if needed
    if isinstance(date, datetime):
        date = date.strftime('%Y-%m-%d')

    # Convert boolean to int for SQLite
    status_int = 1 if status else 0

    # Use INSERT OR REPLACE (upsert)
    query = """
        INSERT INTO logs (habit_id, date, status)
        VALUES (?, ?, ?)
        ON CONFLICT(habit_id, date)
        DO UPDATE SET status = excluded.status
    """

    return db.execute_update(query, (habit_id, date, status_int))


def delete_log(habit_id, date):
    """
    Delete a log entry for a habit on a specific date.

    Args:
        habit_id: The habit ID
        date: Date string in 'YYYY-MM-DD' format or datetime object

    Returns:
        Number of rows affected
    """
    db = get_db()

    # Convert datetime to string if needed
    if isinstance(date, datetime):
        date = date.strftime('%Y-%m-%d')

    query = "DELETE FROM logs WHERE habit_id = ? AND date = ?"
    return db.execute_update(query, (habit_id, date))


def get_habit_streak(habit_id):
    """
    Calculate the current streak for a habit (consecutive days completed up to today).

    Args:
        habit_id: The habit ID

    Returns:
        Dictionary with streak information:
        {
            'current_streak': int,
            'last_completed_date': str or None
        }
    """
    db = get_db()

    # Get all completed logs for this habit, ordered by date descending
    query = """
        SELECT date, status
        FROM logs
        WHERE habit_id = ? AND status = 1
        ORDER BY date DESC
    """
    logs = db.execute_query(query, (habit_id,))

    if not logs:
        return {'current_streak': 0, 'last_completed_date': None}

    # Check if the most recent log is today or yesterday
    today = datetime.now().date()
    streak = 0
    last_completed_date = None

    for log in logs:
        log_date = datetime.strptime(log['date'], '%Y-%m-%d').date()

        if last_completed_date is None:
            # First iteration - check if it's today or in the past
            if log_date > today:
                # Future date, skip it
                continue

            last_completed_date = log_date
            expected_date = log_date

            # Start counting streak
            if log_date == today or log_date == today - timedelta(days=1):
                streak = 1
                expected_date = log_date - timedelta(days=1)
            else:
                # Gap between today and last completed date
                break
        else:
            # Check if this log is consecutive
            if log_date == expected_date:
                streak += 1
                expected_date = log_date - timedelta(days=1)
            else:
                # Gap found, streak is broken
                break

    return {
        'current_streak': streak,
        'last_completed_date': last_completed_date.strftime('%Y-%m-%d') if last_completed_date else None
    }


def save_day_logs(date, habit_statuses):
    """
    Save multiple log entries for a single day.

    Args:
        date: Date string in 'YYYY-MM-DD' format or datetime object
        habit_statuses: Dictionary mapping habit_id to status boolean
                       Example: {1: True, 2: False, 3: True}

    Returns:
        Number of logs saved
    """
    db = get_db()

    # Convert datetime to string if needed
    if isinstance(date, datetime):
        date = date.strftime('%Y-%m-%d')

    count = 0
    for habit_id, status in habit_statuses.items():
        upsert_log(habit_id, date, status)
        count += 1

    return count


def get_completion_stats(habit_id, days=30):
    """
    Get completion statistics for a habit over the last N days.

    Args:
        habit_id: The habit ID
        days: Number of days to look back (default: 30)

    Returns:
        Dictionary with:
        {
            'total_days': int,
            'completed_days': int,
            'completion_rate': float (0-100)
        }
    """
    db = get_db()

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    query = """
        SELECT COUNT(*) as completed_count
        FROM logs
        WHERE habit_id = ?
          AND date >= ?
          AND date <= ?
          AND status = 1
    """

    result = db.execute_query(
        query,
        (habit_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )

    completed_days = result[0]['completed_count'] if result else 0
    completion_rate = (completed_days / days) * 100 if days > 0 else 0

    return {
        'total_days': days,
        'completed_days': completed_days,
        'completion_rate': round(completion_rate, 1)
    }
