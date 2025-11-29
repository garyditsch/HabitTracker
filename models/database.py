import sqlite3
import os
from contextlib import contextmanager
from config import Config


class Database:
    """Database connection and initialization handler."""

    def __init__(self, db_path=None):
        """Initialize database handler with path."""
        self.db_path = db_path or Config.DATABASE_PATH

    def _ensure_instance_dir(self):
        """Ensure the instance directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o755)

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        self._ensure_instance_dir()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """
        Initialize the database with schema from schema.sql.
        Creates tables and indexes if they don't exist.
        """
        self._ensure_instance_dir()

        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        with self.get_connection() as conn:
            conn.executescript(schema_sql)

        print(f"Database initialized at: {self.db_path}")

    def execute_query(self, query, params=None):
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)

        Returns:
            List of sqlite3.Row objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def execute_update(self, query, params=None):
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)

        Returns:
            ID of last inserted row (for INSERT) or number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Return lastrowid for INSERT, rowcount for UPDATE/DELETE
            if cursor.lastrowid > 0:
                return cursor.lastrowid
            return cursor.rowcount


# Global database instance
db = Database()


def init_database():
    """Initialize the database. Called when app starts."""
    db.init_db()


def get_db():
    """Get database instance."""
    return db
