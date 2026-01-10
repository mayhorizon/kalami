#!/usr/bin/env python3
"""Database initialization script for agent state management."""

import sqlite3
import os
import sys

# Default database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent-state.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def init_database(db_path=None):
    """Initialize the database with the schema.

    Args:
        db_path: Path to the SQLite database file. Defaults to DB_PATH.

    Returns:
        tuple: (success: bool, message: str)
    """
    if db_path is None:
        db_path = DB_PATH

    try:
        # Read schema
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        # Create database and execute schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute schema (CREATE TABLE and CREATE INDEX statements)
        cursor.executescript(schema_sql)

        conn.commit()
        conn.close()

        return True, f"Database initialized successfully at {db_path}"

    except FileNotFoundError:
        return False, f"Schema file not found: {SCHEMA_PATH}"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def get_connection(db_path=None):
    """Get a connection to the database.

    Args:
        db_path: Path to the SQLite database file. Defaults to DB_PATH.

    Returns:
        sqlite3.Connection: Database connection
    """
    if db_path is None:
        db_path = DB_PATH

    # Initialize database if it doesn't exist
    if not os.path.exists(db_path):
        success, message = init_database(db_path)
        if not success:
            raise RuntimeError(f"Failed to initialize database: {message}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def vacuum_database(db_path=None):
    """Vacuum the database to reclaim space and optimize.

    Args:
        db_path: Path to the SQLite database file. Defaults to DB_PATH.

    Returns:
        tuple: (success: bool, message: str)
    """
    if db_path is None:
        db_path = DB_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        return True, "Database vacuumed successfully"
    except sqlite3.Error as e:
        return False, f"Vacuum failed: {e}"


def get_db_stats(db_path=None):
    """Get statistics about the database.

    Args:
        db_path: Path to the SQLite database file. Defaults to DB_PATH.

    Returns:
        dict: Statistics including table counts and database size
    """
    if db_path is None:
        db_path = DB_PATH

    if not os.path.exists(db_path):
        return {"error": "Database does not exist"}

    stats = {
        "database_path": db_path,
        "database_size_bytes": os.path.getsize(db_path)
    }

    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()

        # Get row counts for each table
        tables = ['sessions', 'agents', 'tool_calls', 'state_snapshots', 'modifications']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]

        conn.close()
    except Exception as e:
        stats["error"] = str(e)

    return stats


if __name__ == '__main__':
    # Command-line interface
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            db_path = sys.argv[2] if len(sys.argv) > 2 else None
            success, message = init_database(db_path)
            print(message)
            sys.exit(0 if success else 1)

        elif command == 'vacuum':
            db_path = sys.argv[2] if len(sys.argv) > 2 else None
            success, message = vacuum_database(db_path)
            print(message)
            sys.exit(0 if success else 1)

        elif command == 'stats':
            db_path = sys.argv[2] if len(sys.argv) > 2 else None
            stats = get_db_stats(db_path)

            print("\n=== Database Statistics ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
            sys.exit(0)

        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 init_db.py [init|vacuum|stats] [db_path]")
            sys.exit(1)
    else:
        # Default action: initialize database
        success, message = init_database()
        print(message)
        sys.exit(0 if success else 1)
