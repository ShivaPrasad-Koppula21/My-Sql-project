"""
TRAVELNEST Configuration Module
Loads environment variables and application-wide settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)

# Database Configuration
def get_db_credentials():
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "travelnest_db"),
        "backend": os.getenv("DB_BACKEND", "mysql").lower()
    }

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "travelnest_db")

# Fallback mode flag: If MySQL connection is unavailable, can use sqlite for seamless demonstration
# Allowed values: 'mysql' (default) or 'sqlite'
DB_BACKEND = os.getenv("DB_BACKEND", "mysql").lower()
SQLITE_DB_PATH = str(BASE_DIR / "travelnest_demo.db")

# Security & Admin Enrollment
ADMIN_ENROLLMENT_CODE = os.getenv("ADMIN_ENROLLMENT_CODE", "YATRIVO_ADMIN_2026")

# Application Settings
APP_NAME = "Yatrivo"
APP_TAGLINE = "Discover More. Travel Smarter."
APP_VERSION = "3.0.0 — Enterprise Edition"
PAGE_ICON = "🧭"

# Currency settings
DEFAULT_CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
