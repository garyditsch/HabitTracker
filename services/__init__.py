"""Service layer for business logic."""

from .habit_service import (
    get_all_habits,
    get_active_habits,
    get_habit_by_id,
    create_habit,
    update_habit,
    reorder_habits,
    delete_habit,
    hard_delete_habit
)

from .log_service import (
    get_logs_for_date,
    get_logs_for_habit,
    upsert_log,
    delete_log,
    get_habit_streak,
    save_day_logs,
    get_completion_stats,
    get_value_stats
)

from .dashboard_service import (
    get_public_dashboard_data,
    get_admin_tracking_data,
    get_habit_history_chart_data,
    get_yearly_heatmap_data,
    get_archived_habits_data
)

from .cache_service import (
    cache,
    get_cached,
    set_cached,
    invalidate_cache,
    clear_all_cache,
    invalidate_dashboard_cache
)

__all__ = [
    # Habit service
    'get_all_habits',
    'get_active_habits',
    'get_habit_by_id',
    'create_habit',
    'update_habit',
    'reorder_habits',
    'delete_habit',
    'hard_delete_habit',
    # Log service
    'get_logs_for_date',
    'get_logs_for_habit',
    'upsert_log',
    'delete_log',
    'get_habit_streak',
    'save_day_logs',
    'get_completion_stats',
    'get_value_stats',
    # Dashboard service
    'get_public_dashboard_data',
    'get_admin_tracking_data',
    'get_habit_history_chart_data',
    'get_yearly_heatmap_data',
    'get_archived_habits_data',
    # Cache service
    'cache',
    'get_cached',
    'set_cached',
    'invalidate_cache',
    'clear_all_cache',
    'invalidate_dashboard_cache'
]
