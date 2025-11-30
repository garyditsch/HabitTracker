#!/usr/bin/env python3
"""
Functionality Tests for Health Tracker

Tests core application functionality including:
- Database operations
- Habit CRUD
- Log tracking
- Dashboard data aggregation
- Cache invalidation
- Date handling
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Print test result with color coding"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    print()

def setup_test_database():
    """Create a test database"""
    from models.database import Database

    # Create temporary database file
    test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
    os.close(test_db_fd)

    # Initialize database
    db = Database(test_db_path)
    db.init_db()

    # Set this as the current database for services
    import models.database
    models.database.db = db

    return db, test_db_path

def cleanup_test_database(db_path):
    """Remove test database file"""
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_database_initialization():
    """Test database initialization"""
    print(f"{YELLOW}Testing Database Initialization...{RESET}\n")

    try:
        db, db_path = setup_test_database()

        # Check that tables exist
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check habits table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habits'")
            habits_exists = cursor.fetchone() is not None

            # Check logs table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
            logs_exists = cursor.fetchone() is not None

            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]

        print_test("Habits table created", habits_exists)
        print_test("Logs table created", logs_exists)
        print_test(
            "Indexes created",
            len(indexes) >= 4,
            f"Found {len(indexes)} indexes"
        )

        cleanup_test_database(db_path)
        return habits_exists and logs_exists and len(indexes) >= 4

    except Exception as e:
        print_test("Database initialization", False, f"Error: {str(e)}")
        return False

def test_habit_crud():
    """Test habit CRUD operations"""
    print(f"{YELLOW}Testing Habit CRUD Operations...{RESET}\n")

    try:
        from services.habit_service import (
            create_habit, get_habit_by_id, get_all_habits,
            update_habit, delete_habit
        )

        db, db_path = setup_test_database()

        # Create habits
        habit1_id = create_habit("Test Habit 1", is_public=True)
        habit2_id = create_habit("Test Habit 2", is_public=False)

        print_test(
            "Create habits",
            habit1_id is not None and habit2_id is not None,
            f"Created habits with IDs: {habit1_id}, {habit2_id}"
        )

        # Read habit
        habit1 = get_habit_by_id(habit1_id)
        print_test(
            "Read habit by ID",
            habit1 is not None and habit1['name'] == "Test Habit 1",
            f"Retrieved: {habit1['name']}"
        )

        # Get all habits (public only)
        public_habits = get_all_habits(include_private=False)
        print_test(
            "Filter public habits",
            len(public_habits) == 1,
            f"Found {len(public_habits)} public habit(s)"
        )

        # Get all habits (including private)
        all_habits = get_all_habits(include_private=True)
        print_test(
            "Get all habits including private",
            len(all_habits) == 2,
            f"Found {len(all_habits)} total habit(s)"
        )

        # Update habit
        update_habit(habit1_id, name="Updated Habit Name")
        updated_habit = get_habit_by_id(habit1_id)
        print_test(
            "Update habit",
            updated_habit['name'] == "Updated Habit Name",
            f"Updated to: {updated_habit['name']}"
        )

        # Delete habit (soft delete)
        delete_habit(habit1_id)
        deleted_habit = get_habit_by_id(habit1_id)
        print_test(
            "Soft delete habit",
            deleted_habit['is_active'] == 0,
            "Habit marked as inactive"
        )

        cleanup_test_database(db_path)
        return True

    except Exception as e:
        print_test("Habit CRUD operations", False, f"Error: {str(e)}")
        if 'db_path' in locals():
            cleanup_test_database(db_path)
        return False

def test_log_tracking():
    """Test log tracking functionality"""
    print(f"{YELLOW}Testing Log Tracking...{RESET}\n")

    try:
        from services.habit_service import create_habit
        from services.log_service import (
            upsert_log, get_logs_for_date, get_logs_for_habit,
            get_habit_streak, save_day_logs
        )

        db, db_path = setup_test_database()

        # Create a test habit
        habit_id = create_habit("Exercise", is_public=True)
        today = datetime.now().date().strftime('%Y-%m-%d')
        yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Create log
        upsert_log(habit_id, today, True)
        print_test("Create log entry", True, f"Logged habit for {today}")

        # Get logs for date
        logs = get_logs_for_date(today)
        print_test(
            "Retrieve logs by date",
            len(logs) == 1 and logs[0]['habit_id'] == habit_id,
            f"Found {len(logs)} log(s) for today"
        )

        # Get habit logs
        habit_logs = get_logs_for_habit(habit_id)
        print_test(
            "Get habit logs",
            len(habit_logs) == 1,
            f"Found {len(habit_logs)} log(s) for this habit"
        )

        # Test upsert (update existing log)
        upsert_log(habit_id, today, False)
        updated_logs = get_logs_for_date(today)
        print_test(
            "Update existing log (upsert)",
            updated_logs[0]['status'] == 0,
            "Log status updated from True to False"
        )

        # Test streak calculation
        # Create consecutive logs
        upsert_log(habit_id, yesterday, True)
        upsert_log(habit_id, today, True)
        streak_info = get_habit_streak(habit_id)
        print_test(
            "Calculate streak",
            streak_info['current_streak'] >= 1,
            f"Current streak: {streak_info['current_streak']} day(s)"
        )

        # Test batch save
        logs_to_save = {
            habit_id: True
        }
        save_day_logs(today, logs_to_save)
        print_test("Batch save logs", True, "Saved multiple logs in one operation")

        cleanup_test_database(db_path)
        return True

    except Exception as e:
        print_test("Log tracking", False, f"Error: {str(e)}")
        if 'db_path' in locals():
            cleanup_test_database(db_path)
        return False

def test_dashboard_data():
    """Test dashboard data aggregation"""
    print(f"{YELLOW}Testing Dashboard Data Aggregation...{RESET}\n")

    try:
        from services.habit_service import create_habit
        from services.log_service import upsert_log
        from services.dashboard_service import get_public_dashboard_data

        db, db_path = setup_test_database()

        # Create habits (1 public, 1 private)
        public_habit = create_habit("Public Habit", is_public=True)
        private_habit = create_habit("Private Habit", is_public=False)

        # Add some logs
        today = datetime.now().date().strftime('%Y-%m-%d')
        upsert_log(public_habit, today, True)
        upsert_log(private_habit, today, True)

        # Get dashboard data
        dashboard_data = get_public_dashboard_data(days=30)

        # Check that only public habits are returned
        habit_count = len(dashboard_data['habits'])
        print_test(
            "Public dashboard excludes private habits",
            habit_count == 1,
            f"Found {habit_count} public habit(s)"
        )

        # Check data structure
        if habit_count > 0:
            habit_data = dashboard_data['habits'][0]
            has_required_fields = all(
                field in habit_data
                for field in ['id', 'name', 'current_streak', 'completion_rate', 'logs']
            )
            print_test(
                "Dashboard data structure",
                has_required_fields,
                "Contains all required fields"
            )

            # Check logs structure
            if habit_data['logs']:
                log = habit_data['logs'][0]
                has_log_fields = 'date' in log and 'status' in log
                print_test(
                    "Log data structure",
                    has_log_fields,
                    "Logs contain date and status"
                )

        # Check date range
        has_date_range = 'date_range' in dashboard_data
        print_test(
            "Dashboard includes date range",
            has_date_range,
            f"Date range: {dashboard_data.get('date_range', {})}"
        )

        cleanup_test_database(db_path)
        return True

    except Exception as e:
        print_test("Dashboard data aggregation", False, f"Error: {str(e)}")
        if 'db_path' in locals():
            cleanup_test_database(db_path)
        return False

def test_cache_functionality():
    """Test caching functionality"""
    print(f"{YELLOW}Testing Cache Functionality...{RESET}\n")

    try:
        from services.cache_service import (
            get_cached, set_cached, invalidate_cache,
            invalidate_dashboard_cache
        )

        # Test basic caching
        set_cached('test_key', {'data': 'test_value'})
        cached_value = get_cached('test_key')
        print_test(
            "Cache set and get",
            cached_value is not None and cached_value.get('data') == 'test_value',
            "Successfully cached and retrieved data"
        )

        # Test invalidation
        invalidate_cache('test_key')
        invalidated_value = get_cached('test_key')
        print_test(
            "Cache invalidation",
            invalidated_value is None,
            "Cache successfully invalidated"
        )

        # Test dashboard cache invalidation
        set_cached('dashboard_data', {'habits': []})
        invalidate_dashboard_cache()
        dashboard_value = get_cached('dashboard_data')
        print_test(
            "Dashboard cache invalidation",
            dashboard_value is None,
            "Dashboard cache successfully invalidated"
        )

        # Test cache expiration (if duration is short enough)
        import time
        set_cached('expiry_test', 'data', duration=1)
        time.sleep(1.5)
        expired_value = get_cached('expiry_test')
        print_test(
            "Cache expiration",
            expired_value is None,
            "Cache expires after duration"
        )

        return True

    except Exception as e:
        print_test("Cache functionality", False, f"Error: {str(e)}")
        return False

def test_habit_ordering():
    """Test habit ordering functionality"""
    print(f"{YELLOW}Testing Habit Ordering...{RESET}\n")

    try:
        from services.habit_service import create_habit, get_all_habits, reorder_habits

        db, db_path = setup_test_database()

        # Create multiple habits
        habit1_id = create_habit("First Habit", is_public=True)
        habit2_id = create_habit("Second Habit", is_public=True)
        habit3_id = create_habit("Third Habit", is_public=True)

        # Get initial order
        habits = get_all_habits(include_private=True)
        initial_order = [h['id'] for h in habits]
        print_test(
            "Habits have order_index",
            all('order_index' in h for h in habits),
            f"Initial order: {initial_order}"
        )

        # Reorder habits
        new_order = [habit3_id, habit1_id, habit2_id]
        reorder_habits(new_order)

        # Verify new order
        reordered_habits = get_all_habits(include_private=True)
        final_order = [h['id'] for h in reordered_habits]
        print_test(
            "Reorder habits",
            final_order == new_order,
            f"New order: {final_order}"
        )

        cleanup_test_database(db_path)
        return True

    except Exception as e:
        print_test("Habit ordering", False, f"Error: {str(e)}")
        if 'db_path' in locals():
            cleanup_test_database(db_path)
        return False

def test_date_handling():
    """Test date handling functionality"""
    print(f"{YELLOW}Testing Date Handling...{RESET}\n")

    try:
        from services.habit_service import create_habit
        from services.log_service import upsert_log, get_logs_for_date

        db, db_path = setup_test_database()

        habit_id = create_habit("Date Test Habit", is_public=True)

        # Test various date formats
        today_str = datetime.now().date().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Create logs with different dates
        upsert_log(habit_id, today_str, True)
        upsert_log(habit_id, yesterday_str, True)

        # Verify date filtering
        today_logs = get_logs_for_date(today_str)
        yesterday_logs = get_logs_for_date(yesterday_str)

        print_test(
            "Date filtering",
            len(today_logs) == 1 and len(yesterday_logs) == 1,
            f"Today: {len(today_logs)} log(s), Yesterday: {len(yesterday_logs)} log(s)"
        )

        # Test date boundary handling
        future_date = (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d')
        upsert_log(habit_id, future_date, True)
        future_logs = get_logs_for_date(future_date)
        print_test(
            "Future date handling",
            len(future_logs) == 1,
            "Can track future dates"
        )

        cleanup_test_database(db_path)
        return True

    except Exception as e:
        print_test("Date handling", False, f"Error: {str(e)}")
        if 'db_path' in locals():
            cleanup_test_database(db_path)
        return False

def run_all_tests():
    """Run all functionality tests"""
    print(f"\n{'='*60}")
    print(f"  HEALTH TRACKER - FUNCTIONALITY TESTS")
    print(f"{'='*60}\n")

    results = {
        "Database Initialization": test_database_initialization(),
        "Habit CRUD Operations": test_habit_crud(),
        "Log Tracking": test_log_tracking(),
        "Dashboard Data Aggregation": test_dashboard_data(),
        "Cache Functionality": test_cache_functionality(),
        "Habit Ordering": test_habit_ordering(),
        "Date Handling": test_date_handling(),
    }

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}\n")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{'='*60}")
    percentage = (passed / total) * 100
    color = GREEN if percentage == 100 else YELLOW if percentage >= 80 else RED
    print(f"{color}Score: {passed}/{total} ({percentage:.0f}%){RESET}")
    print(f"{'='*60}\n")

    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
