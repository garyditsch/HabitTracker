"""Quick test script to verify database initialization."""

from models import init_database, get_db

if __name__ == '__main__':
    print("Testing database initialization...")

    # Initialize database
    init_database()

    # Verify tables exist
    db = get_db()
    tables = db.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )

    print("\nTables created:")
    for table in tables:
        print(f"  - {table['name']}")

    # Verify indexes exist
    indexes = db.execute_query(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
    )

    print("\nIndexes created:")
    for index in indexes:
        print(f"  - {index['name']}")

    print("\n✓ Database initialization successful!")
