"""
====================================================================
YATRIVO — Enterprise Travel Booking & Trip Management System
Main Entry Point, Security Gatekeeper & Role-Based Router
Tagline: Discover More. Travel Smarter.
====================================================================
"""

import streamlit as st
import os
from config import APP_NAME, APP_TAGLINE, APP_VERSION, PAGE_ICON, DB_HOST, DB_PORT
from database import test_connection, get_backend_type
from auth import (
    is_authenticated,
    is_admin,
    get_current_user,
    logout_session,
    render_auth_page
)
from modules.dashboard import render_dashboard
from modules.destinations import render_destinations
from modules.flights import render_flights
from modules.hotels import render_hotels
from modules.packages import render_packages
from modules.bookings import render_bookings
from modules.trips import render_trips
from modules.reviews import render_reviews
from modules.admin import render_admin
from modules.analytics import render_analytics


# ========================================================
# 1. STREAMLIT PAGE CONFIGURATION
# ========================================================
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================================
# 2. YATRIVO ENTERPRISE DESIGN SYSTEM (CYAN / TEAL / NAVY)
# ========================================================
st.markdown("""
<style>
    /* Main Background & Base Typography */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Streamlit Main Container Spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        max-width: 1300px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B132B !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Streamlit Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stButton > button:hover {
        border-color: #06B6D4 !important;
        box-shadow: 0 4px 14px rgba(6, 182, 212, 0.25) !important;
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #06B6D4 0%, #0D9488 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    /* Form Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(6, 182, 212, 0.12) !important;
        color: #38BDF8 !important;
        border-bottom: 2px solid #06B6D4 !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0B132B;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #06B6D4;
    }
</style>
""", unsafe_allow_html=True)


# ========================================================
# 3. MANDATORY AUTHENTICATION GATEKEEPER
# ========================================================
# If not authenticated, render the dedicated Yatrivo login/register screen
# and immediately stop. Unauthenticated users cannot view any protected pages.
if not is_authenticated():
    render_auth_page()
    st.stop()


# ========================================================
# 4. AUTHENTICATED SESSION CONTEXT & ROLE EXTRACTION
# ========================================================
current_user = get_current_user()
user_role = current_user.get("role", "customer") if current_user else "customer"
user_name = current_user.get("full_name", "Traveler") if current_user else "Traveler"
user_email = current_user.get("email", "") if current_user else ""

# Default navigation routing based on role
if "nav_selection" not in st.session_state:
    if user_role == "admin":
        st.session_state["nav_selection"] = "Admin Dashboard"
    else:
        st.session_state["nav_selection"] = "Customer Dashboard"

# Test Database Connection Status for Diagnostic Indicator
db_conn_ok, db_backend_mode, db_msg = test_connection()


# ========================================================
# 5. SIDEBAR NAVIGATION & PROFILE CONTROLS
# ========================================================
with st.sidebar:
    # Yatrivo Compass Logo & Brand Header
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        col_sb1, col_sb_logo, col_sb2 = st.columns([1, 1.6, 1])
        with col_sb_logo:
            st.image(logo_path, use_container_width=True)

    st.markdown(f"""
    <div style="padding: 4px 4px 14px 4px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px; text-align: center;">
        <div style="font-size: 1.55rem; font-weight: 900; letter-spacing: 0.08em; color: #FFFFFF; line-height: 1.1;">
            {APP_NAME}
        </div>
        <div style="font-size: 0.72rem; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px;">
            {APP_TAGLINE}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Authenticated User Profile Card
    role_badge = "🛡️ Administrator" if user_role == "admin" else "👤 Verified Customer"
    badge_bg = "rgba(239, 68, 68, 0.15)" if user_role == "admin" else "rgba(16, 185, 129, 0.15)"
    badge_color = "#F87171" if user_role == "admin" else "#34D399"

    st.markdown(f"""
    <div style="
        background: #1E293B;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">{user_name}</div>
            <span style="font-size: 0.7rem; background: {badge_bg}; color: {badge_color}; padding: 2px 8px; border-radius: 9999px; font-weight: 700;">
                {role_badge}
            </span>
        </div>
        <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 12px; overflow: hidden; text-overflow: ellipsis;">
            {user_email}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True, key="btn_sidebar_logout"):
        logout_session()
        st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # --- Role-Based Navigation Options ---
    nav_options = []
    if user_role == "admin":
        nav_options.append(("🛡️ Admin Control Panel", "Admin Dashboard"))
        nav_options.append(("🏠 View Customer Dashboard", "Customer Dashboard"))
    else:
        nav_options.append(("🏠 Customer Dashboard", "Customer Dashboard"))

    # Shared Travel Modules
    nav_options.extend([
        ("🗺️ Explore Destinations", "Explore Destinations"),
        ("✈️ Flight Explorer", "Flight Explorer"),
        ("🏨 Hotel Explorer", "Hotel Explorer"),
        ("🎒 Travel Packages", "Travel Packages"),
        ("📑 My Bookings", "My Bookings"),
        ("🧭 My Trips & Planner", "My Trips"),
        ("⭐ Reviews & Ratings", "Reviews & Ratings"),
        ("📈 Analytics & Reports", "Analytics & Reports"),
    ])

    current_nav = st.session_state.get("nav_selection", "Customer Dashboard" if user_role != "admin" else "Admin Dashboard")

    st.markdown("<div style='font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #64748B; letter-spacing: 0.05em; margin-bottom: 8px;'>Navigation Menu</div>", unsafe_allow_html=True)
    for label, target_page in nav_options:
        is_active = (current_nav == target_page)
        btn_prefix = "👉 " if is_active else ""
        if st.button(f"{btn_prefix}{label}", key=f"nav_btn_{target_page}", use_container_width=True):
            st.session_state["nav_selection"] = target_page
            st.rerun()

    # Database Diagnostic Indicator in Sidebar
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0 14px 0;'/>", unsafe_allow_html=True)
    if db_backend_mode == "mysql":
        st.markdown(f"""
        <div style="font-size: 0.78rem; color: #34D399; display: flex; align-items: center; gap: 6px;">
            <span>🟢</span> <b>Database: MySQL 8.0</b> (Connected)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size: 0.78rem; color: #38BDF8; display: flex; align-items: center; gap: 6px;">
            <span>🟢</span> <b>Database: Demo Mode</b> (All Data Loaded)
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div style='font-size: 0.72rem; color: #64748B; margin-top: 14px; text-align: center;'>{APP_NAME} v{APP_VERSION}</div>", unsafe_allow_html=True)


# ========================================================
# 6. SERVER-SIDE ROUTING & ROLE GUARDS
# ========================================================
current_page = st.session_state.get("nav_selection", "Customer Dashboard" if user_role != "admin" else "Admin Dashboard")

# Strict Server-Side Role Guard: Prevent customers from accessing Admin Portal
if current_page == "Admin Dashboard":
    if not is_admin():
        st.error("⛔ Access Denied: Administrator role required to view the Admin Dashboard.")
        st.session_state["nav_selection"] = "Customer Dashboard"
        st.rerun()
    else:
        render_admin()

elif current_page in ("Customer Dashboard", "Home Dashboard"):
    render_dashboard()

elif current_page == "Explore Destinations":
    render_destinations()

elif current_page == "Flight Explorer":
    render_flights()

elif current_page == "Hotel Explorer":
    render_hotels()

elif current_page == "Travel Packages":
    render_packages()

elif current_page == "My Bookings":
    render_bookings()

elif current_page == "My Trips":
    render_trips()

elif current_page == "Reviews & Ratings":
    render_reviews()

elif current_page == "Analytics & Reports":
    render_analytics()

else:
    # Default fallback
    if user_role == "admin":
        render_admin()
    else:
        render_dashboard()
