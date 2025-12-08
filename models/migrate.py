"""Database migration utilities for Health Tracker."""

import sqlite3
from pathlib import Path
from models import get_db


def get_current_schema_version(conn):
    """Get the current schema version from the database."""
    try:
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.OperationalError:
        # Table doesn't exist, this is version 0
        return 0


def create_schema_version_table(conn):
    """Create the schema_version table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def migration_001_add_value_tracking(conn):
    """
    Migration 001: Add value tracking columns.

    Adds:
    - habits.tracks_value (BOOLEAN)
    - habits.value_unit (TEXT)
    - logs.value (REAL)
    """
    print("Running migration 001: Add value tracking columns...")

    # Check if columns already exist
    cursor = conn.execute("PRAGMA table_info(habits)")
    habit_columns = {row[1] for row in cursor.fetchall()}

    cursor = conn.execute("PRAGMA table_info(logs)")
    log_columns = {row[1] for row in cursor.fetchall()}

    # Add columns to habits table if they don't exist
    if 'tracks_value' not in habit_columns:
        conn.execute("ALTER TABLE habits ADD COLUMN tracks_value BOOLEAN DEFAULT 0 NOT NULL")
        print("  ✓ Added habits.tracks_value column")
    else:
        print("  - habits.tracks_value already exists, skipping")

    if 'value_unit' not in habit_columns:
        conn.execute("ALTER TABLE habits ADD COLUMN value_unit TEXT")
        print("  ✓ Added habits.value_unit column")
    else:
        print("  - habits.value_unit already exists, skipping")

    # Add column to logs table if it doesn't exist
    if 'value' not in log_columns:
        conn.execute("ALTER TABLE logs ADD COLUMN value REAL")
        print("  ✓ Added logs.value column")
    else:
        print("  - logs.value already exists, skipping")

    conn.commit()
    print("Migration 001 completed successfully!")


def migration_002_add_value_aggregation_type(conn):
    """
    Migration 002: Add value aggregation type column.

    Adds:
    - habits.value_aggregation_type (TEXT) - 'absolute' or 'cumulative'
    """
    print("Running migration 002: Add value aggregation type column...")

    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(habits)")
    habit_columns = {row[1] for row in cursor.fetchall()}

    # Add column to habits table if it doesn't exist
    if 'value_aggregation_type' not in habit_columns:
        conn.execute("ALTER TABLE habits ADD COLUMN value_aggregation_type TEXT DEFAULT 'absolute' NOT NULL")
        print("  ✓ Added habits.value_aggregation_type column")
    else:
        print("  - habits.value_aggregation_type already exists, skipping")

    conn.commit()
    print("Migration 002 completed successfully!")


# Migration registry - add new migrations here in order
MIGRATIONS = [
    migration_001_add_value_tracking,
    migration_002_add_value_aggregation_type,
]


def run_migrations():
    """Run all pending database migrations."""
    db = get_db()

    with db.get_connection() as conn:
        # Ensure schema_version table exists
        create_schema_version_table(conn)

        # Get current version
        current_version = get_current_schema_version(conn)
        print(f"Current schema version: {current_version}")

        # Run pending migrations
        for i, migration in enumerate(MIGRATIONS, start=1):
            if i > current_version:
                print(f"\n--- Running migration {i} ---")
                migration(conn)

                # Record migration
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (i,)
                )
                conn.commit()
                print(f"✓ Migration {i} applied\n")
            else:
                print(f"✓ Migration {i} already applied")

        # Get final version
        final_version = get_current_schema_version(conn)

        if final_version == current_version:
            print("\n✓ Database is up to date!")
        else:
            print(f"\n✓ Database migrated from version {current_version} to {final_version}")


if __name__ == "__main__":
    print("=== Health Tracker Database Migration ===\n")
    run_migrations()
