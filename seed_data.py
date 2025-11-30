"""Seed the database with sample data for testing."""

from datetime import datetime, timedelta
from services import create_habit, upsert_log


def seed_database():
    """Add sample habits and logs for testing."""
    print("Seeding database with sample data...")

    # Create some public habits
    habit1_id = create_habit("Morning Exercise", is_public=True)
    habit2_id = create_habit("Drink Water (8 glasses)", is_public=True)
    habit3_id = create_habit("Read for 30 min", is_public=True)
    habit4_id = create_habit("Private Journal", is_public=False)  # This won't show on public dashboard

    print(f"✓ Created habits:")
    print(f"  - Morning Exercise (ID: {habit1_id})")
    print(f"  - Drink Water (ID: {habit2_id})")
    print(f"  - Read for 30 min (ID: {habit3_id})")
    print(f"  - Private Journal (ID: {habit4_id}, private)")

    # Add logs for the past 30 days
    today = datetime.now().date()

    habits = [
        (habit1_id, 0.8),  # 80% completion rate
        (habit2_id, 0.9),  # 90% completion rate
        (habit3_id, 0.6),  # 60% completion rate
        (habit4_id, 0.7),  # 70% completion rate (private)
    ]

    import random
    random.seed(42)  # Consistent random data

    for habit_id, completion_rate in habits:
        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            # Random completion based on rate
            status = random.random() < completion_rate
            upsert_log(habit_id, date, status)

    print(f"\n✓ Added 30 days of log data for each habit")
    print("\n✓ Database seeded successfully!")
    print("\nYou can now view the dashboard at: http://localhost:5000/")


if __name__ == '__main__':
    seed_database()
