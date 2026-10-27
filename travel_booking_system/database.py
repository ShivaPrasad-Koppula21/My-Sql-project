"""
TRAVELNEST Database Engine & Helper Module
Provides connection management, schema initialization, and parameterized query execution.
Designed for MySQL with seamless offline demonstration support.
"""

import os
import sqlite3
import mysql.connector
from mysql.connector import Error as MySQLError
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union

from config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_BACKEND,
    SQLITE_DB_PATH,
    BASE_DIR,
    get_db_credentials
)


_MYSQL_AVAILABLE = None


def is_mysql_available(force_refresh: bool = False) -> bool:
    """Checks whether the MySQL server is reachable with the configured credentials."""
    global _MYSQL_AVAILABLE
    if _MYSQL_AVAILABLE is True and not force_refresh:
        return True
    try:
        conn = get_mysql_connection(database=None)
        conn.close()
        _MYSQL_AVAILABLE = True
    except Exception:
        _MYSQL_AVAILABLE = False
    return _MYSQL_AVAILABLE


def get_backend_type() -> str:
    """Returns 'mysql' if available and configured, otherwise falls back to 'sqlite' demo mode."""
    creds = get_db_credentials()
    mode = creds.get("backend", "mysql").lower()
    if mode == "sqlite":
        return "sqlite"
    if is_mysql_available():
        return "mysql"
    # Graceful viva demonstration fallback
    return "sqlite"


def get_mysql_connection(database: Optional[str] = None):
    """Establishes and returns a direct connection to the MySQL database."""
    creds = get_db_credentials()
    db_target = creds["database"] if database is None and database != "" else database
    params = {
        "host": creds["host"],
        "port": creds["port"],
        "user": creds["user"],
        "password": creds["password"],
        "charset": "utf8mb4",
        "autocommit": False
    }
    if db_target:
        params["database"] = db_target
    return mysql.connector.connect(**params)


def test_connection() -> Tuple[bool, str, str]:
    """
    Tests database connectivity.
    Returns: (is_primary_mysql: bool, active_backend: str, message: str)
    """
    if is_mysql_available():
        try:
            conn = get_mysql_connection(database=None)
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            ver = cursor.fetchone()[0]
            cursor.close()
            creds = get_db_credentials()
            return True, "mysql", f"Connected to MySQL 8.0 Server (v{ver}) at {creds['host']}:{creds['port']}"
        except Exception:
            pass

    # Verify SQLite Demo Database
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return True, "sqlite", f"Demo Database connected at {SQLITE_DB_PATH}"
    except Exception as e:
        return False, "none", f"Database error: {str(e)}"


def init_db() -> Tuple[bool, str]:
    """
    Initializes the database schema.
    In MySQL, creates the database if needed, then executes schema.sql tables.
    In SQLite, creates the corresponding tables.
    """
    backend = get_backend_type()
    schema_file = BASE_DIR / "schema.sql"

    if backend == "mysql":
        try:
            # 1. Connect without specific DB to create database
            conn = get_mysql_connection(database=None)
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.close()
            conn.close()

            # 2. Connect to the created database and execute tables
            conn = get_mysql_connection(database=DB_NAME)
            cursor = conn.cursor()
            with open(schema_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split statements by semicolon
            statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
            for stmt in statements:
                # Skip CREATE DATABASE or USE statements since we are already connected to DB_NAME
                if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE"):
                    continue
                try:
                    cursor.execute(stmt)
                except MySQLError as err:
                    # Ignore table already exists or harmless warnings
                    pass

            conn.commit()
            cursor.close()
            conn.close()
            return True, f"MySQL database '{DB_NAME}' initialized successfully."
        except Exception as e:
            return False, f"MySQL Initialization Error: {str(e)}"

    else:
        # SQLite Initialization
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            _init_sqlite_schema(cursor)
            conn.commit()
            conn.close()
            return True, "SQLite database schema initialized successfully."
        except Exception as e:
            return False, f"SQLite Initialization Error: {str(e)}"


def _init_sqlite_schema(cursor):
    """Creates SQLite tables compatible with MySQL schema for offline resilience."""
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        account_status TEXT NOT NULL DEFAULT 'active',
        phone TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT NULL
    );

    CREATE TABLE IF NOT EXISTS admin_enrollment_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'pending',
        reviewed_by INTEGER DEFAULT NULL,
        reviewed_at TIMESTAMP DEFAULT NULL,
        rejection_reason TEXT DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS destinations (
        destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state_country TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Heritage',
        description TEXT NOT NULL,
        best_time_to_visit TEXT DEFAULT 'Oct - Mar',
        estimated_budget REAL NOT NULL DEFAULT 15000.00,
        image_url TEXT DEFAULT NULL,
        rating REAL NOT NULL DEFAULT 4.50,
        is_featured INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS flights (
        flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number TEXT NOT NULL UNIQUE,
        airline TEXT NOT NULL,
        source_city TEXT NOT NULL,
        destination_city TEXT NOT NULL,
        departure_time TIMESTAMP NOT NULL,
        arrival_time TIMESTAMP NOT NULL,
        duration_minutes INTEGER NOT NULL,
        stops INTEGER NOT NULL DEFAULT 0,
        travel_class TEXT NOT NULL DEFAULT 'Economy',
        price REAL NOT NULL,
        seats_available INTEGER NOT NULL DEFAULT 60,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS hotels (
        hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        destination_id INTEGER NOT NULL,
        city TEXT NOT NULL,
        address TEXT NOT NULL,
        star_rating INTEGER NOT NULL DEFAULT 4,
        property_type TEXT NOT NULL DEFAULT 'Boutique Hotel',
        amenities TEXT NOT NULL,
        price_per_night REAL NOT NULL,
        image_url TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS hotel_rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hotel_id INTEGER NOT NULL,
        room_type TEXT NOT NULL,
        capacity INTEGER NOT NULL DEFAULT 2,
        price_per_night REAL NOT NULL,
        available_rooms INTEGER NOT NULL DEFAULT 10,
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS travel_packages (
        package_id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        package_type TEXT NOT NULL DEFAULT 'Domestic',
        duration_days INTEGER NOT NULL DEFAULT 4,
        duration_nights INTEGER NOT NULL DEFAULT 3,
        itinerary_summary TEXT NOT NULL,
        inclusions TEXT NOT NULL,
        price REAL NOT NULL,
        max_group_size INTEGER NOT NULL DEFAULT 20,
        image_url TEXT DEFAULT NULL,
        is_featured INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activities (
        activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Sightseeing',
        duration_hours REAL NOT NULL DEFAULT 3.0,
        location TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS trips (
        trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        destination_id INTEGER DEFAULT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        budget REAL NOT NULL DEFAULT 50000.00,
        notes TEXT DEFAULT NULL,
        status TEXT NOT NULL DEFAULT 'Planning',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS trip_destinations (
        trip_dest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        destination_id INTEGER NOT NULL,
        visit_order INTEGER NOT NULL DEFAULT 1,
        stay_days INTEGER NOT NULL DEFAULT 2,
        FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE,
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_reference TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        trip_id INTEGER DEFAULT NULL,
        booking_type TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        item_title TEXT NOT NULL,
        booking_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        travel_start_date DATE NOT NULL,
        travel_end_date DATE NOT NULL,
        num_guests INTEGER NOT NULL DEFAULT 1,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Confirmed',
        cancellation_reason TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        title TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE (user_id, target_type, target_id)
    );
    """)


def execute_query(
    query: str,
    params: Optional[Union[tuple, list, dict]] = None,
    fetch: Optional[str] = None,
    commit: bool = False
) -> Any:
    """
    Executes a parameterized SQL query safely.
    Works seamlessly across MySQL and SQLite by standardizing parameter placeholders.
    :param query: SQL query with %s placeholders
    :param params: tuple, list, or dict of parameters
    :param fetch: 'all', 'one', or None
    :param commit: bool to commit transaction
    :return: list of dicts, single dict, lastrowid, or None
    """
    backend = get_backend_type()
    params = params or ()

    if backend == "mysql":
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)

            result = None
            if fetch == "all":
                result = cursor.fetchall()
            elif fetch == "one":
                result = cursor.fetchone()
            elif commit:
                conn.commit()
                result = cursor.lastrowid

            cursor.close()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and conn.is_connected():
                conn.close()

    else:
        # SQLite execution
        conn = None
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # SQLite uses '?' instead of '%s'
            sqlite_query = query.replace("%s", "?")
            cursor.execute(sqlite_query, params)

            result = None
            if fetch == "all":
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            elif fetch == "one":
                row = cursor.fetchone()
                result = dict(row) if row else None
            elif commit:
                conn.commit()
                result = cursor.lastrowid

            cursor.close()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()


def fetch_all(query: str, params: Optional[Union[tuple, list]] = None) -> List[Dict[str, Any]]:
    """Helper to fetch all records as a list of dictionaries."""
    res = execute_query(query, params, fetch="all")
    return res if res is not None else []


def fetch_one(query: str, params: Optional[Union[tuple, list]] = None) -> Optional[Dict[str, Any]]:
    """Helper to fetch a single record as a dictionary."""
    return execute_query(query, params, fetch="one")


def execute_commit(query: str, params: Optional[Union[tuple, list]] = None) -> int:
    """Helper to execute an INSERT/UPDATE/DELETE statement with commit and return lastrowid."""
    return execute_query(query, params, commit=True)


def fetch_dataframe(query: str, params: Optional[Union[tuple, list]] = None) -> pd.DataFrame:
    """Helper to execute query and return a Pandas DataFrame directly."""
    records = fetch_all(query, params)
    return pd.DataFrame(records) if records else pd.DataFrame()


def get_table_counts() -> Dict[str, int]:
    """Returns the record count for each major table in the database."""
    tables = [
        "users",
        "destinations",
        "flights",
        "hotels",
        "hotel_rooms",
        "travel_packages",
        "activities",
        "trips",
        "trip_destinations",
        "bookings",
        "reviews",
        "admin_enrollment_requests"
    ]
    counts = {}
    for table in tables:
        try:
            row = fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            counts[table] = row["cnt"] if row else 0
        except Exception:
            counts[table] = 0
    return counts
