"""
VOYANTA Migration Script
Adds account_status column to users and creates admin_enrollment_requests table.
Ensures bootstrap accounts and active statuses.
"""

import datetime
import database
from auth import hash_password, generate_salt

def run_migration():
    print("=" * 60)
    print("VOYANTA DATABASE SCHEMA MIGRATION")
    print("=" * 60)

    # 1. Add account_status to users table in MySQL if missing
    try:
        cols = [r['Field'] for r in database.fetch_all("DESCRIBE users")]
        if 'account_status' not in cols:
            database.execute_commit(
                "ALTER TABLE users ADD COLUMN account_status ENUM('active', 'pending', 'suspended', 'rejected') NOT NULL DEFAULT 'active' AFTER role;"
            )
            print("[OK] Added 'account_status' column to users table.")
        else:
            print("[INFO] 'account_status' column already exists in users table.")
    except Exception as e:
        print(f"[NOTE] Migration check on users table: {e}")

    # 2. Create admin_enrollment_requests table
    req_table_sql = """
    CREATE TABLE IF NOT EXISTS admin_enrollment_requests (
        request_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
        reviewed_by INT DEFAULT NULL,
        reviewed_at DATETIME DEFAULT NULL,
        rejection_reason VARCHAR(255) DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
        INDEX idx_aer_user (user_id),
        INDEX idx_aer_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    try:
        database.execute_commit(req_table_sql)
        print("[OK] 'admin_enrollment_requests' table created / verified.")
    except Exception as e:
        print(f"[ERROR] Creating admin_enrollment_requests: {e}")

    # 3. Ensure all existing users are set to active
    try:
        database.execute_commit("UPDATE users SET account_status = 'active' WHERE account_status IS NULL OR account_status = '';")
        print("[OK] Confirmed existing users are 'active'.")
    except Exception as e:
        print(f"[NOTE] Setting active status: {e}")

    # 4. Bootstrap Voyanta specific accounts (admin@voyanta.com & user@voyanta.com)
    accounts = [
        ("admin@voyanta.com", "Admin@123", "Voyanta Chief Administrator", "admin", "active", "+91 98000 00001"),
        ("user@voyanta.com", "User@123", "Aarav Sharma", "customer", "active", "+91 98000 00002")
    ]
    for email, pwd, name, role, status, phone in accounts:
        existing = database.fetch_one("SELECT user_id FROM users WHERE LOWER(email) = %s", (email.lower(),))
        if not existing:
            salt = generate_salt()
            pwd_hash = hash_password(pwd, salt)
            now = datetime.datetime.now()
            database.execute_commit(
                """INSERT INTO users (email, password_hash, salt, full_name, role, account_status, phone, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (email.lower(), pwd_hash, salt, name, role, status, phone, now)
            )
            print(f"[OK] Created bootstrap account: {email} ({role})")
        else:
            database.execute_commit(
                "UPDATE users SET account_status = 'active', role = %s WHERE LOWER(email) = %s",
                (role, email.lower())
            )
            print(f"[INFO] Account {email} verified active.")

    print("=" * 60)
    print("VOYANTA MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_migration()
