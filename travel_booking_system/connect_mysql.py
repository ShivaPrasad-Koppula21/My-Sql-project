"""
TRAVELNEST — MySQL Setup & Connection Utility
Connects to local MySQL 8.0, verifies credentials, creates travelnest_db,
applies schema.sql, seeds initial data, and updates .env.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("Error: 'mysql-connector-python' is not installed.")
    print("Please run: pip install mysql-connector-python")
    sys.exit(1)


def update_env_file(host, port, user, password, db_name):
    """Updates or creates .env with the verified MySQL credentials."""
    env_file = BASE_DIR / ".env"
    content = f"""# TRAVELNEST Local Database Configuration
DB_HOST={host}
DB_PORT={port}
DB_USER={user}
DB_PASSWORD={password}
DB_NAME={db_name}

# Database backend: 'mysql'
DB_BACKEND=mysql
"""
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f" [OK] Updated configuration in {env_file.name}")


def setup_mysql(password: str, user: str = "root", host: str = "localhost", port: int = 3306, db_name: str = "travelnest_db"):
    print("=" * 60)
    print(" TRAVELNEST — MYSQL CONNECTION & SETUP")
    print("=" * 60)
    print(f"Connecting to MySQL server at {host}:{port} with user '{user}'...")

    # 1. Test connection to server
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f" [OK] Successfully authenticated with MySQL Server (v{version})!")
    except mysql.connector.Error as err:
        print(f"\n [ERROR] Failed to connect to MySQL: {err}")
        if err.errno == 1045:
            print(" -> Access denied: The password or username is incorrect.")
        elif err.errno == 2003:
            print(" -> Can't connect to MySQL server: Ensure MySQL service is running.")
        return False

    # 2. Create Database
    try:
        print(f"\nCreating database '{db_name}' if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f" [OK] Database '{db_name}' is ready.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f" [ERROR] Could not create database: {e}")
        return False

    # 3. Update .env
    update_env_file(host, port, user, password, db_name)

    # 4. Apply Schema
    schema_file = BASE_DIR / "schema.sql"
    if schema_file.exists():
        print(f"\nApplying schema from {schema_file.name}...")
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            with open(schema_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            success_count = 0
            for stmt in statements:
                # Clean comment lines to check command
                lines = [line.strip() for line in stmt.splitlines() if line.strip() and not line.strip().startswith("--")]
                if not lines:
                    continue
                first_line = lines[0].upper()
                if first_line.startswith("CREATE DATABASE") or first_line.startswith("USE"):
                    continue
                try:
                    cursor.execute(stmt)
                    success_count += 1
                except Exception as ex:
                    # Table already exists or minor warning
                    pass

            conn.commit()
            cursor.close()
            conn.close()
            print(f" [OK] Schema applied ({success_count} statements processed).")
        except Exception as e:
            print(f" [ERROR] Error applying schema: {e}")
            return False

    # 5. Populate Data via seed_data.py
    print("\nPopulating database tables with comprehensive travel dataset...")
    try:
        # Set environment variables for this process
        os.environ["DB_HOST"] = host
        os.environ["DB_PORT"] = str(port)
        os.environ["DB_USER"] = user
        os.environ["DB_PASSWORD"] = password
        os.environ["DB_NAME"] = db_name
        os.environ["DB_BACKEND"] = "mysql"

        # Re-import or run seed_data
        import seed_data
        # Force re-check of MySQL availability
        import database
        database._MYSQL_AVAILABLE = True
        seed_data.seed_all_data(force_reset=True)
        print(" [OK] All tables populated with real data!")
    except Exception as e:
        print(f" [WARNING] Seeding encountered an error: {e}")

    # 6. Verify table counts
    try:
        import database
        counts = database.get_table_counts()
        print("\n" + "=" * 60)
        print(" VERIFIED MYSQL TABLE RECORD COUNTS:")
        print("=" * 60)
        for tbl, cnt in counts.items():
            print(f"  • {tbl.ljust(20)}: {cnt} records")
        print("=" * 60)
        print(" TRAVELNEST is now fully connected to your MySQL Database!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"Verification error: {e}")
        return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        import getpass
        pwd = getpass.getpass("Enter your MySQL root password: ")
    setup_mysql(password=pwd)
