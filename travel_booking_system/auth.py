"""
====================================================================
YATRIVO — Authentication & Cybersecurity Access Control Engine
Role-Based Access Control (RBAC), PBKDF2 Password Security,
Two-Stage Administrator Enrollment Verification & Approval Workflow
====================================================================
"""

import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, Tuple, List
import streamlit as st

from config import (
    ADMIN_ENROLLMENT_CODE,
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION
)
from database import fetch_one, fetch_all, execute_commit, execute_query


# ========================================================
# 1. CRYPTOGRAPHIC SECURITY HELPERS
# ========================================================

def generate_salt() -> str:
    """Generates a cryptographically secure 16-byte random hexadecimal salt."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Hashes a password with salt using PBKDF2-HMAC-SHA256 (100,000 iterations)."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time verification of candidate password against expected PBKDF2 hash."""
    computed_hash = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)


def verify_admin_code(provided_code: str) -> bool:
    """
    Validates provided administrator invitation/enrollment code against
    server environment secret using constant-time string comparison.
    """
    if not provided_code or not ADMIN_ENROLLMENT_CODE:
        return False
    return secrets.compare_digest(provided_code.strip(), ADMIN_ENROLLMENT_CODE.strip())


# ========================================================
# 2. USER REGISTRATION & ROLE LIFECYCLE
# ========================================================

def register_user(
    email: str,
    password: str,
    full_name: str,
    phone: Optional[str] = None,
    role: str = "customer",
    admin_code: Optional[str] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Registers a new user account with strict role validation.
    - Customer registrations create active customer accounts.
    - Administrator registrations require server secret verification AND
      create a 'pending' approval request. An active administrator must approve it.
    Returns: (success: bool, message: str, user_id: Optional[int])
    """
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean or "." not in email_clean:
        return False, "Please provide a valid email address.", None

    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    if not full_name.strip():
        return False, "Full name cannot be blank.", None

    # Check for duplicate email
    existing = fetch_one("SELECT user_id FROM users WHERE LOWER(email) = %s", (email_clean,))
    if existing:
        return False, f"An account with email '{email_clean}' already exists. Please sign in.", None

    role_clean = role.strip().lower()
    if role_clean not in ("customer", "admin"):
        role_clean = "customer"

    # --- ADMINISTRATOR ENROLLMENT VALIDATION ---
    if role_clean == "admin":
        if not admin_code or not verify_admin_code(admin_code):
            # Track failed attempt
            failed_attempts = st.session_state.get("failed_admin_codes", 0) + 1
            st.session_state["failed_admin_codes"] = failed_attempts
            return False, "Invalid Administrator Enrollment Code. Administrator registration denied.", None

        # Admin account is created with 'pending' status awaiting authorization
        account_status = "pending"
    else:
        account_status = "active"

    salt = generate_salt()
    pwd_hash = hash_password(password, salt)
    now = datetime.datetime.now()

    insert_user_sql = """
        INSERT INTO users (email, password_hash, salt, full_name, role, account_status, phone, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        user_id = execute_commit(
            insert_user_sql,
            (email_clean, pwd_hash, salt, full_name.strip(), role_clean, account_status, phone.strip() if phone else None, now)
        )

        # If admin, queue record in admin_enrollment_requests table
        if role_clean == "admin":
            execute_commit(
                """INSERT INTO admin_enrollment_requests (user_id, requested_at, status)
                   VALUES (%s, %s, 'pending')""",
                (user_id, now)
            )
            return (
                True,
                "Administrator enrollment request submitted! For security, your account is pending approval by an active administrator before you can log in.",
                user_id
            )

        return True, "Registration successful! You can now log in.", user_id
    except Exception as e:
        return False, f"Registration failed due to a database error: {str(e)}", None


# ========================================================
# 3. AUTHENTICATION & LOGIN LOGIC
# ========================================================

def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticates a user against MySQL database.
    Checks password hash and validates account status.
    Returns: (success: bool, user_data: Optional[Dict], message: str)
    """
    email_clean = email.strip().lower()
    if not email_clean or not password:
        return False, None, "Please provide both email and password."

    user = fetch_one("SELECT * FROM users WHERE LOWER(email) = %s", (email_clean,))
    if not user:
        return False, None, "Invalid email or password."

    salt = user["salt"]
    expected_hash = user["password_hash"]

    if not verify_password(password, salt, expected_hash):
        return False, None, "Invalid email or password."

    # Validate Account Status
    account_status = user.get("account_status", "active")
    if account_status == "pending":
        return False, None, "Your administrator enrollment request is pending approval by an authorized administrator."
    elif account_status == "rejected":
        return False, None, "Your administrator registration request was rejected by an administrator."
    elif account_status == "suspended":
        return False, None, "Your account has been suspended. Please contact security administration."
    elif account_status != "active":
        return False, None, "Your account is not active. Please contact administrator."

    # Update last_login timestamp
    now = datetime.datetime.now()
    execute_commit("UPDATE users SET last_login = %s WHERE user_id = %s", (now, user["user_id"]))

    user_data = {
        "user_id": user["user_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "account_status": user.get("account_status", "active"),
        "phone": user.get("phone", "")
    }
    return True, user_data, "Login successful!"


# ========================================================
# 4. SESSION & ROLE ACCESS MANAGEMENT
# ========================================================

def login_session(user_data: Dict[str, Any]):
    """Stores user information in Streamlit session state and sets target dashboard."""
    st.session_state["user"] = user_data
    st.session_state["is_authenticated"] = True

    # Immediate redirect to respective dashboard based on role
    if user_data.get("role") == "admin":
        st.session_state["nav_selection"] = "Admin Dashboard"
    else:
        st.session_state["nav_selection"] = "Customer Dashboard"


def logout_session():
    """Clears all authentication state from session and resets navigation."""
    st.session_state["user"] = None
    st.session_state["is_authenticated"] = False
    st.session_state["nav_selection"] = "Login"
    for key in ["selected_flight", "selected_hotel", "selected_package"]:
        if key in st.session_state:
            del st.session_state[key]


def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns currently authenticated user from session state or None."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Server-side check: Returns True if active user session is authenticated."""
    return bool(st.session_state.get("is_authenticated") and st.session_state.get("user"))


def is_admin() -> bool:
    """Server-side check: Returns True only if authenticated user has active admin role."""
    user = get_current_user()
    return bool(user and user.get("role") == "admin" and user.get("account_status") == "active")


# ========================================================
# 5. ADMINISTRATOR ENROLLMENT APPROVAL WORKFLOW
# ========================================================

def get_admin_enrollment_requests(status: str = "pending") -> List[Dict[str, Any]]:
    """Fetches administrator enrollment requests joined with user details."""
    query = """
        SELECT r.request_id, r.user_id, r.requested_at, r.status, r.reviewed_by, r.reviewed_at, r.rejection_reason,
               u.full_name, u.email, u.phone
        FROM admin_enrollment_requests r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.status = %s
        ORDER BY r.requested_at DESC
    """
    return fetch_all(query, (status,))


def approve_admin_request(request_id: int, reviewer_admin_id: int) -> Tuple[bool, str]:
    """
    Approves a pending administrator enrollment request.
    Activates user account with admin privileges in a database transaction.
    """
    req = fetch_one("SELECT * FROM admin_enrollment_requests WHERE request_id = %s", (request_id,))
    if not req:
        return False, "Enrollment request not found."
    if req["status"] != "pending":
        return False, f"Request is already {req['status']}."

    user_id = req["user_id"]
    now = datetime.datetime.now()
    try:
        # Update request
        execute_commit(
            """UPDATE admin_enrollment_requests
               SET status = 'approved', reviewed_by = %s, reviewed_at = %s
               WHERE request_id = %s""",
            (reviewer_admin_id, now, request_id)
        )
        # Activate user
        execute_commit(
            """UPDATE users SET account_status = 'active', role = 'admin' WHERE user_id = %s""",
            (user_id,)
        )
        return True, "Administrator account approved and activated successfully!"
    except Exception as e:
        return False, f"Approval transaction failed: {str(e)}"


def reject_admin_request(request_id: int, reviewer_admin_id: int, reason: str = "Request denied by administrator") -> Tuple[bool, str]:
    """Rejects a pending administrator enrollment request and marks user rejected."""
    req = fetch_one("SELECT * FROM admin_enrollment_requests WHERE request_id = %s", (request_id,))
    if not req:
        return False, "Enrollment request not found."

    user_id = req["user_id"]
    now = datetime.datetime.now()
    try:
        execute_commit(
            """UPDATE admin_enrollment_requests
               SET status = 'rejected', reviewed_by = %s, reviewed_at = %s, rejection_reason = %s
               WHERE request_id = %s""",
            (reviewer_admin_id, now, reason, request_id)
        )
        execute_commit(
            """UPDATE users SET account_status = 'rejected' WHERE user_id = %s""",
            (user_id,)
        )
        return True, "Administrator request rejected."
    except Exception as e:
        return False, f"Rejection transaction failed: {str(e)}"


# ========================================================
# 6. UI: DEDICATED AUTHENTICATION SCREEN
# ========================================================

def render_auth_page():
    """Renders the primary, gatekeeper authentication screen for Yatrivo."""
    import os
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

    # Center Logo and Custom Brand Header
    col_l1, col_logo, col_l2 = st.columns([1, 0.4, 1])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    st.markdown(f"""
    <div style="text-align: center; margin: 10px auto 26px auto; max-width: 680px;">
        <h1 style="color: #FFFFFF; font-size: 2.6rem; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 6px 0;">
            {APP_NAME}
        </h1>
        <div style="color: #38BDF8; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;">
            {APP_TAGLINE}
        </div>
        <p style="color: #94A3B8; font-size: 1.05rem; line-height: 1.6; margin: 0;">
            Sign in to access your curated travel itineraries, bookings, and enterprise analytics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, col_form, _ = st.columns([1, 2.2, 1])

    with col_form:
        tab_login, tab_register, tab_quick = st.tabs([
            "🔑 Sign In",
            "📝 Create Account",
            "⚡ Evaluation Demo Accounts"
        ])

        # ----------------------------------------------------
        # TAB 1: SIGN IN
        # ----------------------------------------------------
        with tab_login:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.form("yatrivo_login_form"):
                email = st.text_input("Email Address", placeholder="user@yatrivo.com")
                password = st.text_input("Password", type="password", placeholder="Enter your account password")

                submit_login = st.form_submit_button("Sign In to Yatrivo", use_container_width=True)

                if submit_login:
                    success, user_data, msg = authenticate_user(email, password)
                    if success and user_data:
                        login_session(user_data)
                        st.success(f"Welcome back, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error(msg)

            with st.expander("❓ Forgot Password or Need Access?"):
                st.markdown("""
                <div style="font-size: 0.88rem; color: #94A3B8; line-height: 1.6;">
                    • <b>Customer Password Reset:</b> Contact Yatrivo Concierge at <code>support@yatrivo.com</code>.<br/>
                    • <b>Administrator Account Inquiries:</b> Administrator access requires authorization by an active systems admin.
                </div>
                """, unsafe_allow_html=True)

        # ----------------------------------------------------
        # TAB 2: CREATE ACCOUNT (CUSTOMER / ADMINISTRATOR)
        # ----------------------------------------------------
        with tab_register:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            account_type = st.radio(
                "Select Account Type",
                ["👤 Customer Account", "🛡️ Administrator Account"],
                horizontal=True
            )

            is_admin_reg = "Administrator" in account_type

            if is_admin_reg:
                st.markdown("""
                <div style="
                    background: rgba(239, 68, 68, 0.08);
                    border: 1px solid rgba(239, 68, 68, 0.25);
                    border-radius: 10px;
                    padding: 12px 16px;
                    margin-bottom: 14px;
                ">
                    <div style="font-weight: 700; color: #F87171; font-size: 0.9rem; margin-bottom: 4px;">
                        🛡️ Restricted Administrator Enrollment
                    </div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5;">
                        Administrator registration requires a valid invitation code configured by the system.
                        Upon submission, your account will enter <b>pending status</b> until approved by an active administrator.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.form("yatrivo_register_form"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Aarav Sharma")
                reg_email = st.text_input("Email Address", placeholder="e.g. traveler@yatrivo.com")
                reg_phone = st.text_input("Phone Number (Optional)", placeholder="+91 98765 43210")
                reg_pwd = st.text_input("Create Password (min. 6 chars)", type="password")
                reg_pwd2 = st.text_input("Confirm Password", type="password")

                admin_code_input = None
                if is_admin_reg:
                    admin_code_input = st.text_input(
                        "Administrator Enrollment Code (Server Secret)",
                        type="password",
                        help="Enter the enrollment code provided in the server .env configuration."
                    )

                submit_reg = st.form_submit_button("Create Account", use_container_width=True)

                if submit_reg:
                    if reg_pwd != reg_pwd2:
                        st.error("Passwords do not match. Please re-enter.")
                    elif is_admin_reg and not admin_code_input:
                        st.error("Administrator enrollment code is mandatory for administrator registration.")
                    else:
                        role_to_reg = "admin" if is_admin_reg else "customer"
                        success, msg, u_id = register_user(
                            email=reg_email,
                            password=reg_pwd,
                            full_name=reg_name,
                            phone=reg_phone,
                            role=role_to_reg,
                            admin_code=admin_code_input
                        )
                        if success:
                            if role_to_reg == "customer":
                                st.success(msg)
                                # Automatically sign in active customer
                                succ_auth, u_data, _ = authenticate_user(reg_email, reg_pwd)
                                if succ_auth and u_data:
                                    login_session(u_data)
                                    st.rerun()
                            else:
                                st.info(msg)
                        else:
                            st.error(msg)

        # ----------------------------------------------------
        # TAB 3: ONE-CLICK QUICK EVALUATION DEMO ACCOUNTS
        # ----------------------------------------------------
        with tab_quick:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.caption("Pre-seeded demonstration profiles for instant evaluation:")

            # Admin Card
            st.markdown("""
            <div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <b style="color: #38BDF8; font-size: 0.95rem;">🛡️ Administrator Role</b>
                    <span style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.2); color: #38BDF8; padding: 2px 8px; border-radius: 9999px;">Active</span>
                </div>
                <div style="font-size: 0.85rem; color: #F1F5F9; font-family: monospace;">admin@yatrivo.com / Admin@123</div>
                <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">Full CRUD on catalog, booking management, approve pending administrator requests.</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Sign In as Administrator (Chief Admin)", use_container_width=True, key="btn_quick_yatrivo_admin"):
                # Try admin@yatrivo.com or fallback to admin@voyanta.com / admin@travelnest.com
                success, u_data, _ = authenticate_user("admin@yatrivo.com", "Admin@123")
                if not success:
                    success, u_data, _ = authenticate_user("admin@voyanta.com", "Admin@123")
                if not success:
                    success, u_data, _ = authenticate_user("admin@travelnest.com", "Admin@123")
                if success and u_data:
                    login_session(u_data)
                    st.rerun()
                else:
                    st.error("Could not authenticate demo admin account. Please verify database connection.")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # Customer Card
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <b style="color: #34D399; font-size: 0.95rem;">👤 Customer Role (Aarav Sharma)</b>
                    <span style="font-size: 0.75rem; background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 2px 8px; border-radius: 9999px;">Active</span>
                </div>
                <div style="font-size: 0.85rem; color: #F1F5F9; font-family: monospace;">user@yatrivo.com / User@123</div>
                <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">Personal travel bookings, flight/hotel booking engine, budget planner, reviews.</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🌟 Sign In as Customer (Aarav Sharma)", use_container_width=True, key="btn_quick_yatrivo_user"):
                success, u_data, _ = authenticate_user("user@yatrivo.com", "User@123")
                if not success:
                    success, u_data, _ = authenticate_user("user@voyanta.com", "User@123")
                if not success:
                    success, u_data, _ = authenticate_user("user@travelnest.com", "User@123")
                if success and u_data:
                    login_session(u_data)
                    st.rerun()
                else:
                    st.error("Could not authenticate demo customer account. Please verify database connection.")
