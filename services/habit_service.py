"""Habit service for CRUD operations on habits."""

from models import get_db


def get_all_habits(include_private=False):
    """
    Get all habits ordered by order_index.

    Args:
        include_private: If False, only returns habits where is_public=True.
                        Defaults to False for security.

    Returns:
        List of habit rows
    """
    db = get_db()

    if include_private:
        query = """
            SELECT id, name, is_active, is_public, order_index, tracks_value, value_unit, value_aggregation_type, created_at
            FROM habits
            ORDER BY order_index ASC, created_at ASC
        """
        return db.execute_query(query)
    else:
        query = """
            SELECT id, name, is_active, is_public, order_index, tracks_value, value_unit, value_aggregation_type, created_at
            FROM habits
            WHERE is_public = 1
            ORDER BY order_index ASC, created_at ASC
        """
        return db.execute_query(query)


def get_active_habits(include_private=True):
    """
    Get only active habits ordered by order_index.

    Args:
        include_private: If True, returns both public and private habits.
                        If False, only returns public habits.

    Returns:
        List of active habit rows
    """
    db = get_db()

    if include_private:
        query = """
            SELECT id, name, is_active, is_public, order_index, tracks_value, value_unit, value_aggregation_type, created_at
            FROM habits
            WHERE is_active = 1
            ORDER BY order_index ASC, created_at ASC
        """
        return db.execute_query(query)
    else:
        query = """
            SELECT id, name, is_active, is_public, order_index, tracks_value, value_unit, value_aggregation_type, created_at
            FROM habits
            WHERE is_active = 1 AND is_public = 1
            ORDER BY order_index ASC, created_at ASC
        """
        return db.execute_query(query)


def get_habit_by_id(habit_id):
    """
    Get a single habit by ID.

    Args:
        habit_id: The habit ID

    Returns:
        Habit row or None if not found
    """
    db = get_db()
    query = """
        SELECT id, name, is_active, is_public, order_index, tracks_value, value_unit, value_aggregation_type, created_at
        FROM habits
        WHERE id = ?
    """
    results = db.execute_query(query, (habit_id,))
    return results[0] if results else None


def create_habit(name, is_public=True, tracks_value=False, value_unit=None, value_aggregation_type='absolute'):
    """
    Create a new habit with auto-assigned order_index.

    Args:
        name: Habit name (required)
        is_public: Whether habit should appear on public dashboard (default: True)
        tracks_value: Whether habit tracks numeric values (default: False)
        value_unit: Unit for tracked values, e.g., "pushups", "lbs" (optional)
        value_aggregation_type: 'absolute' or 'cumulative' (default: 'absolute')

    Returns:
        ID of newly created habit
    """
    db = get_db()

    # Get the max order_index to append new habit at the end
    max_order_query = "SELECT MAX(order_index) as max_order FROM habits"
    result = db.execute_query(max_order_query)
    max_order = result[0]['max_order'] if result and result[0]['max_order'] is not None else -1
    next_order = max_order + 1

    query = """
        INSERT INTO habits (name, is_public, is_active, order_index, tracks_value, value_unit, value_aggregation_type)
        VALUES (?, ?, 1, ?, ?, ?, ?)
    """
    return db.execute_update(query, (
        name,
        1 if is_public else 0,
        next_order,
        1 if tracks_value else 0,
        value_unit,
        value_aggregation_type
    ))


def update_habit(habit_id, **kwargs):
    """
    Update habit properties.

    Args:
        habit_id: The habit ID to update
        **kwargs: Fields to update (name, is_active, is_public, order_index)

    Returns:
        Number of rows affected
    """
    db = get_db()

    # Build dynamic UPDATE query based on provided kwargs
    # Using a whitelist approach for security
    allowed_fields = {
        'name': 'name = ?',
        'is_active': 'is_active = ?',
        'is_public': 'is_public = ?',
        'order_index': 'order_index = ?',
        'tracks_value': 'tracks_value = ?',
        'value_unit': 'value_unit = ?',
        'value_aggregation_type': 'value_aggregation_type = ?'
    }

    updates = []
    values = []

    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(allowed_fields[field])
            # Convert boolean to int for SQLite
            if field in ['is_active', 'is_public', 'tracks_value'] and isinstance(value, bool):
                values.append(1 if value else 0)
            else:
                values.append(value)

    if not updates:
        return 0

    values.append(habit_id)
    # Join pre-validated update clauses (no f-string interpolation)
    query = "UPDATE habits SET " + ", ".join(updates) + " WHERE id = ?"

    return db.execute_update(query, tuple(values))


def reorder_habits(habit_ids):
    """
    Update order_index for multiple habits based on their position in the list.

    Args:
        habit_ids: List of habit IDs in desired order

    Returns:
        Number of habits updated
    """
    db = get_db()
    updated_count = 0

    with db.get_connection() as conn:
        cursor = conn.cursor()
        for index, habit_id in enumerate(habit_ids):
            cursor.execute(
                "UPDATE habits SET order_index = ? WHERE id = ?",
                (index, habit_id)
            )
            updated_count += cursor.rowcount

    return updated_count


def delete_habit(habit_id):
    """
    Soft delete a habit (set is_active to False).

    Args:
        habit_id: The habit ID to delete

    Returns:
        Number of rows affected
    """
    db = get_db()
    query = "UPDATE habits SET is_active = 0 WHERE id = ?"
    return db.execute_update(query, (habit_id,))


def hard_delete_habit(habit_id):
    """
    Permanently delete a habit and all its logs (CASCADE).
    Use with caution - this cannot be undone.

    Args:
        habit_id: The habit ID to delete

    Returns:
        Number of rows affected
    """
    db = get_db()
    query = "DELETE FROM habits WHERE id = ?"
    return db.execute_update(query, (habit_id,))
