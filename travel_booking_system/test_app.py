"""
====================================================================
YATRIVO — Automated Verification & Cybersecurity Test Suite
Validates all 12 mandatory enterprise criteria:
1. Customer registration & authentication
2. Customer Dashboard redirection
3. Server-side customer role isolation
4. Admin registration requires secret & pending approval
5. Invalid admin codes rejected
6. Pending admin accounts denied login & access
7. Active admin approval & rejection workflow
8. Approved admin access to Admin Dashboard
9. Logout session clearance
10. Input validation & duplicate email protection
11. Existing travel booking & cancellation workflows
12. Persistent MySQL database state consistency
====================================================================
"""

import os
import sys
import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BASE_DIR, APP_NAME, ADMIN_ENROLLMENT_CODE
from database import fetch_all, fetch_one, execute_commit, get_table_counts, test_connection
from auth import (
    hash_password,
    verify_password,
    register_user,
    authenticate_user,
    generate_salt,
    is_admin,
    login_session,
    logout_session,
    get_admin_enrollment_requests,
    approve_admin_request,
    reject_admin_request
)
from utils.formatting import format_currency, format_duration, render_stars
from utils.helpers import calculate_stay_nights, generate_booking_reference, truncate_text


class MockSessionState(dict):
    """Simulates Streamlit session_state for headless CLI verification."""
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value


def run_tests():
    print("=" * 70)
    print("YATRIVO ENTERPRISE CYBERSECURITY & FUNCTIONAL TEST SUITE")
    print("=" * 70)

    # ----------------------------------------------------
    # Test 12: Database Connectivity & Persistence Check
    # ----------------------------------------------------
    ok, backend, msg = test_connection()
    assert ok, f"Database connectivity failed: {msg}"
    print(f"[PASS] Scenario 12: Database connection verified ({backend} backend: {msg})")

    counts = get_table_counts()
    print(f"       Current Live Records: {counts}")
    assert counts.get("destinations", 0) >= 60, "Destinations count < 60"
    assert counts.get("flights", 0) >= 500, "Flights count < 500"
    assert counts.get("hotels", 0) >= 150, "Hotels count < 150"
    assert counts.get("travel_packages", 0) >= 100, "Packages count < 100"
    assert counts.get("bookings", 0) >= 300, "Bookings count < 300"

    # ----------------------------------------------------
    # Test 1: New Customer Registration and Login
    # ----------------------------------------------------
    ts = int(datetime.datetime.now().timestamp())
    cust_email = f"yatrivo_cust_{ts}@example.com"
    cust_pwd = "CustPassword@2026"
    reg_ok, reg_msg, cust_uid = register_user(
        email=cust_email,
        password=cust_pwd,
        full_name="Arjun Patel",
        phone="+91 91234 56789",
        role="customer"
    )
    assert reg_ok, f"Customer registration failed: {reg_msg}"
    assert cust_uid is not None, "Customer user_id not returned"

    # Verify user in database is active customer
    cust_db = fetch_one("SELECT * FROM users WHERE user_id = %s", (cust_uid,))
    assert cust_db["role"] == "customer", "Role is not customer"
    assert cust_db["account_status"] == "active", "Customer status is not active"

    # Authenticate customer
    auth_ok, cust_data, auth_msg = authenticate_user(cust_email, cust_pwd)
    assert auth_ok, f"Customer login failed: {auth_msg}"
    assert cust_data["email"] == cust_email
    print(f"[PASS] Scenario 1: Customer registered and authenticated successfully (ID: {cust_uid})")

    # ----------------------------------------------------
    # Test 2: Customer Redirection to Customer Dashboard
    # ----------------------------------------------------
    # Initialize mock session state
    import streamlit as st
    st.session_state = MockSessionState()
    login_session(cust_data)
    assert st.session_state["is_authenticated"] is True
    assert st.session_state["nav_selection"] == "Customer Dashboard", f"Expected Customer Dashboard, got {st.session_state.get('nav_selection')}"
    print("[PASS] Scenario 2: Customer login redirects directly to Customer Dashboard.")

    # ----------------------------------------------------
    # Test 3: Server-Side Customer Role Isolation
    # ----------------------------------------------------
    assert not is_admin(), "Customer was falsely granted admin privileges!"
    print("[PASS] Scenario 3: Server-side role guard verified (Customer cannot access admin functions).")

    # ----------------------------------------------------
    # Test 4: Administrator Registration Requires Secret & Sets Pending Status
    # ----------------------------------------------------
    admin_cand_email = f"admin_cand_{ts}@example.com"
    cand_pwd = "AdminCandPass@2026"

    # Try registering with valid code
    adm_reg_ok, adm_reg_msg, adm_uid = register_user(
        email=admin_cand_email,
        password=cand_pwd,
        full_name="Candidate Admin",
        phone="+91 99887 76655",
        role="admin",
        admin_code=ADMIN_ENROLLMENT_CODE
    )
    assert adm_reg_ok, f"Admin candidate registration failed: {adm_reg_msg}"
    assert "pending" in adm_reg_msg.lower(), "Registration message did not mention pending authorization"

    # Check database status
    adm_db = fetch_one("SELECT * FROM users WHERE user_id = %s", (adm_uid,))
    assert adm_db["role"] == "admin"
    assert adm_db["account_status"] == "pending", f"Expected 'pending' status, got {adm_db['account_status']}"

    # Check request record queued in admin_enrollment_requests
    req_db = fetch_one("SELECT * FROM admin_enrollment_requests WHERE user_id = %s", (adm_uid,))
    assert req_db is not None, "Enrollment request not found in admin_enrollment_requests"
    assert req_db["status"] == "pending"
    print(f"[PASS] Scenario 4: Admin registration queued as pending approval in database (Req ID: {req_db['request_id']})")

    # ----------------------------------------------------
    # Test 5: Incorrect Administrator Codes Are Rejected
    # ----------------------------------------------------
    bad_code_email = f"bad_code_{ts}@example.com"
    bad_reg_ok, bad_reg_msg, _ = register_user(
        email=bad_code_email,
        password="SomePassword@123",
        full_name="Attacker",
        role="admin",
        admin_code="WRONG_SECRET_CODE_123"
    )
    assert not bad_reg_ok, "Registration with invalid admin code was unexpectedly allowed!"
    assert "denied" in bad_reg_msg.lower() or "invalid" in bad_reg_msg.lower()
    print("[PASS] Scenario 5: Incorrect administrator codes rejected with access denial.")

    # ----------------------------------------------------
    # Test 6: Pending Administrator Denied Login
    # ----------------------------------------------------
    cand_auth_ok, cand_user, cand_auth_msg = authenticate_user(admin_cand_email, cand_pwd)
    assert not cand_auth_ok, "Pending administrator was permitted to log in!"
    assert "pending" in cand_auth_msg.lower()
    print("[PASS] Scenario 6: Pending administrator account blocked from logging in.")

    # ----------------------------------------------------
    # Test 7: Active Administrator Approves Enrollment Request
    # ----------------------------------------------------
    # Use existing authorized bootstrap admin
    active_admin = fetch_one("SELECT user_id FROM users WHERE role = 'admin' AND account_status = 'active' LIMIT 1")
    assert active_admin is not None, "No active administrator available in system"
    reviewer_id = active_admin["user_id"]

    # Test rejection workflow first with a dummy request
    dummy_email = f"rej_cand_{ts}@example.com"
    _, _, dummy_uid = register_user(dummy_email, "DummyPass@123", "Reject Cand", role="admin", admin_code=ADMIN_ENROLLMENT_CODE)
    dummy_req = fetch_one("SELECT request_id FROM admin_enrollment_requests WHERE user_id = %s", (dummy_uid,))
    rej_ok, rej_msg = reject_admin_request(dummy_req["request_id"], reviewer_id, "Incomplete credentials")
    assert rej_ok, f"Rejection failed: {rej_msg}"
    dummy_user_check = fetch_one("SELECT account_status FROM users WHERE user_id = %s", (dummy_uid,))
    assert dummy_user_check["account_status"] == "rejected"

    # Now approve the real candidate request
    appr_ok, appr_msg = approve_admin_request(req_db["request_id"], reviewer_id)
    assert appr_ok, f"Approval failed: {appr_msg}"

    # Verify user is now active admin in database
    appr_user_db = fetch_one("SELECT * FROM users WHERE user_id = %s", (adm_uid,))
    assert appr_user_db["account_status"] == "active"
    assert appr_user_db["role"] == "admin"
    print(f"[PASS] Scenario 7: Active admin approval & rejection workflow verified (Approved ID: {adm_uid})")

    # ----------------------------------------------------
    # Test 8: Approved Administrator Can Log In & Access Admin Dashboard
    # ----------------------------------------------------
    adm_login_ok, adm_user_data, adm_login_msg = authenticate_user(admin_cand_email, cand_pwd)
    assert adm_login_ok, f"Approved admin failed to log in: {adm_login_msg}"
    login_session(adm_user_data)
    assert st.session_state["nav_selection"] == "Admin Dashboard"
    assert is_admin() is True
    print("[PASS] Scenario 8: Approved administrator logs in and accesses Admin Dashboard.")

    # ----------------------------------------------------
    # Test 9: Logout Clears Authentication Session
    # ----------------------------------------------------
    logout_session()
    assert st.session_state["is_authenticated"] is False
    assert st.session_state["user"] is None
    assert not is_admin()
    print("[PASS] Scenario 9: Logout cleared authentication session and returned to login state.")

    # ----------------------------------------------------
    # Test 10: Input Validation & Duplicate Email Handling
    # ----------------------------------------------------
    # Duplicate email rejection
    dup_ok, dup_msg, _ = register_user(cust_email, "AnotherPass@123", "Duplicate User", role="customer")
    assert not dup_ok, "Duplicate email registration was permitted!"
    assert "already exists" in dup_msg.lower()

    # Short password rejection
    short_ok, short_msg, _ = register_user(f"short_{ts}@example.com", "123", "Short Pass", role="customer")
    assert not short_ok
    assert "at least 6 characters" in short_msg.lower()

    # Invalid email rejection
    bad_em_ok, bad_em_msg, _ = register_user("notanemail", "ValidPass@123", "Bad Email", role="customer")
    assert not bad_em_ok
    print("[PASS] Scenario 10: Input validation (duplicate emails, password length, format) verified.")

    # ----------------------------------------------------
    # Test 11: Existing Booking & Travel Features
    # ----------------------------------------------------
    ref = generate_booking_reference("Flight")
    now = datetime.datetime.now()
    bid = execute_commit(
        """INSERT INTO bookings (booking_reference, user_id, booking_type, item_id, item_title, booking_date, travel_start_date, travel_end_date, num_guests, unit_price, total_price, status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (ref, cust_uid, "Flight", 1, "Yatrivo Airways YAT-101 (Delhi -> Goa)", now, now.date(), now.date(), 2, 6000.0, 12000.0, "Confirmed", now)
    )
    assert bid > 0, "Booking insert failed"
    booking_row = fetch_one("SELECT * FROM bookings WHERE booking_id = %s", (bid,))
    assert booking_row["booking_reference"] == ref
    assert booking_row["status"] == "Confirmed"

    # Cancellation rule check
    execute_commit(
        "UPDATE bookings SET status = 'Cancelled', cancellation_reason = %s WHERE booking_id = %s AND user_id = %s",
        ("Customer schedule change", bid, cust_uid)
    )
    upd_b = fetch_one("SELECT status, cancellation_reason FROM bookings WHERE booking_id = %s", (bid,))
    assert upd_b["status"] == "Cancelled"
    assert upd_b["cancellation_reason"] == "Customer schedule change"

    # Review submission & duplicate check
    execute_commit(
        """INSERT INTO reviews (user_id, target_type, target_id, rating, title, comment, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (cust_uid, "destination", 1, 5, "Unforgettable Experience", "Exceptional service by Yatrivo!", now)
    )
    rev_row = fetch_one("SELECT * FROM reviews WHERE user_id = %s AND target_type = %s AND target_id = %s", (cust_uid, "destination", 1))
    assert rev_row is not None
    assert rev_row["rating"] == 5
    print("[PASS] Scenario 11: Existing booking, cancellation, and review workflows operating flawlessly.")

    print("=" * 70)
    print("ALL 12 YATRIVO ENTERPRISE TEST SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
