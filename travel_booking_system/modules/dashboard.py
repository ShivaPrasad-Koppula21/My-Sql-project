"""
====================================================================
YATRIVO — Customer Experience Dashboard Module
Dedicated personalized traveler portal, itinerary summaries,
recent booking activity, search explorer, and featured collections.
====================================================================
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one
from utils.formatting import format_currency, render_stars, get_status_badge, format_datetime
from utils.helpers import get_image_url, truncate_text
from auth import get_current_user, is_authenticated


def render_dashboard():
    user = get_current_user()
    user_name = user["full_name"] if user else "Traveler"
    uid = user["user_id"] if user else None

    # --- Hero Welcome Header ---
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 41, 59, 0.90) 50%, rgba(13, 148, 136, 0.45) 100%),
                    url('https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80') center/cover;
        border-radius: 20px;
        padding: 36px 36px;
        margin-bottom: 24px;
        border: 1px solid rgba(6, 182, 212, 0.25);
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
    ">
        <div style="max-width: 820px;">
            <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 14px; border-radius: 9999px; background: rgba(6, 182, 212, 0.15); border: 1px solid #06B6D4; color: #38BDF8; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                <span>🧭</span> <span>Yatrivo Travel Concierge</span>
            </div>
            <h1 style="color: #FFFFFF; font-size: 2.4rem; font-weight: 800; margin: 0 0 8px 0; line-height: 1.2;">
                Welcome back, {user_name}!
            </h1>
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6; margin: 0 0 20px 0;">
                Your personal travel hub. Track upcoming itineraries, manage live bookings, and discover curated luxury escapes across 60+ destinations worldwide.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Global Quick Search Bar ---
    search_query = st.text_input(
        "🔍 Search across Yatrivo (Destinations, Flights, Hotels, or Packages)",
        placeholder="Search destinations (e.g., Goa, Paris), airlines (IndiGo, Emirates), or hotels...",
        key="dash_global_search"
    )
    if search_query:
        # Search results routing
        st.markdown(f"**Results matching '{search_query}':**")
        sc1, sc2 = st.columns(2)
        with sc1:
            matching_dests = fetch_all(
                "SELECT * FROM destinations WHERE name LIKE %s OR city LIKE %s OR state_country LIKE %s LIMIT 3",
                (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            )
            if matching_dests:
                st.caption(f"Found {len(matching_dests)} matching destinations:")
                for d in matching_dests:
                    if st.button(f"📍 {d['name']} ({d['city']}, {d['state_country']})", key=f"q_dest_{d['destination_id']}"):
                        st.session_state["nav_selection"] = "Explore Destinations"
                        st.session_state["search_destination_filter"] = d["name"]
                        st.rerun()
        with sc2:
            matching_pkgs = fetch_all(
                "SELECT * FROM travel_packages WHERE title LIKE %s OR itinerary_summary LIKE %s LIMIT 3",
                (f"%{search_query}%", f"%{search_query}%")
            )
            if matching_pkgs:
                st.caption(f"Found {len(matching_pkgs)} matching packages:")
                for p in matching_pkgs:
                    if st.button(f"🎒 {p['title']} ({format_currency(p['price'])})", key=f"q_pkg_{p['package_id']}"):
                        st.session_state["nav_selection"] = "Travel Packages"
                        st.session_state["selected_package_id"] = p["package_id"]
                        st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --- Personalized Metric Cards ---
    col1, col2, col3, col4 = st.columns(4)

    if uid:
        user_bookings = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE user_id = %s", (uid,))
        active_trips = fetch_one("SELECT COUNT(*) as cnt FROM trips WHERE user_id = %s AND status IN ('Upcoming', 'Planning')", (uid,))
        total_spent = fetch_one("SELECT SUM(total_price) as total FROM bookings WHERE user_id = %s AND status != 'Cancelled'", (uid,))
        reviews_given = fetch_one("SELECT COUNT(*) as cnt FROM reviews WHERE user_id = %s", (uid,))

        with col1:
            st.metric("Total Bookings", user_bookings["cnt"] if user_bookings else 0, delta="My History")
        with col2:
            st.metric("Active Trips", active_trips["cnt"] if active_trips else 0, delta="Planned / Upcoming")
        with col3:
            spent_val = total_spent["total"] if total_spent and total_spent["total"] else 0
            st.metric("Travel Spend", format_currency(spent_val), delta="Verified Bookings")
        with col4:
            st.metric("Reviews Shared", reviews_given["cnt"] if reviews_given else 0, delta="Feedback Given")
    else:
        dest_cnt = fetch_one("SELECT COUNT(*) as cnt FROM destinations")
        hotel_cnt = fetch_one("SELECT COUNT(*) as cnt FROM hotels")
        pkg_cnt = fetch_one("SELECT COUNT(*) as cnt FROM travel_packages")
        flight_cnt = fetch_one("SELECT COUNT(*) as cnt FROM flights")

        with col1:
            st.metric("Destinations", dest_cnt["cnt"] if dest_cnt else 60, delta="Verified")
        with col2:
            st.metric("Hotels & Stays", hotel_cnt["cnt"] if hotel_cnt else 150, delta="Properties")
        with col3:
            st.metric("Curated Packages", pkg_cnt["cnt"] if pkg_cnt else 100, delta="Itineraries")
        with col4:
            st.metric("Flights", flight_cnt["cnt"] if flight_cnt else 500, delta="Daily Routes")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- Quick Actions Row ---
    st.subheader("⚡ Quick Navigation Shortcuts")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("🗺️ Explore Destinations", use_container_width=True, key="btn_q_dest"):
            st.session_state["nav_selection"] = "Explore Destinations"
            st.rerun()
    with q2:
        if st.button("✈️ Search Flights", use_container_width=True, key="btn_q_flight"):
            st.session_state["nav_selection"] = "Flight Explorer"
            st.rerun()
    with q3:
        if st.button("🏨 Find Hotels", use_container_width=True, key="btn_q_hotel"):
            st.session_state["nav_selection"] = "Hotel Explorer"
            st.rerun()
    with q4:
        if st.button("🧭 Plan a New Trip", use_container_width=True, key="btn_q_trip"):
            st.session_state["nav_selection"] = "My Trips"
            st.rerun()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- Two Columns: Upcoming Trips & Recent Bookings ---
    sec_left, sec_right = st.columns([1.1, 1.3])

    with sec_left:
        st.markdown("### 🧭 My Upcoming Trips")
        if uid:
            upcoming_trips = fetch_all(
                """SELECT t.*, d.name as dest_name, d.city
                   FROM trips t
                   LEFT JOIN destinations d ON t.destination_id = d.destination_id
                   WHERE t.user_id = %s
                   ORDER BY t.start_date ASC LIMIT 3""",
                (uid,)
            )
            if upcoming_trips:
                for trip in upcoming_trips:
                    st.markdown(f"""
                    <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <b style="color: #F8FAFC; font-size: 1rem;">{trip['title']}</b>
                            <span style="font-size: 0.78rem; color: #38BDF8; font-weight: 600;">{trip['status']}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8; margin: 4px 0;">
                            📍 {trip.get('dest_name') or 'Custom Destinations'} • {trip['start_date']} to {trip['end_date']}
                        </div>
                        <div style="font-size: 0.82rem; color: #64748B;">
                            Budget: <b style="color: #34D399;">{format_currency(trip['budget'])}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("View All Trips & Budget Tracker", key="btn_dash_view_trips", use_container_width=True):
                    st.session_state["nav_selection"] = "My Trips"
                    st.rerun()
            else:
                st.info("No upcoming trips planned yet. Click 'Plan a New Trip' above to build a custom itinerary!")
        else:
            st.info("Sign in to track custom multi-destination trips and budget utilization.")

    with sec_right:
        st.markdown("### 📑 Recent Booking Activity")
        if uid:
            recent_bks = fetch_all(
                """SELECT * FROM bookings
                   WHERE user_id = %s
                   ORDER BY booking_date DESC LIMIT 4""",
                (uid,)
            )
            if recent_bks:
                for b in recent_bks:
                    status_badge = get_status_badge(b["status"])
                    st.markdown(f"""
                    <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-family: monospace; font-size: 0.85rem; color: #38BDF8; font-weight: 700;">{b['booking_reference']}</span>
                            <span>{status_badge}</span>
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #F1F5F9;">{b['item_title']}</div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #94A3B8; margin-top: 6px;">
                            <span>Category: {b['booking_type']}</span>
                            <span style="font-weight: 700; color: #34D399;">{format_currency(b['total_price'])}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("Manage All Bookings & Cancellations", key="btn_dash_view_bks", use_container_width=True):
                    st.session_state["nav_selection"] = "My Bookings"
                    st.rerun()
            else:
                st.info("No reservations found in your account history yet. Book a flight, hotel, or package to get started!")
        else:
            st.info("Sign in to view real-time reservation records and cancellation options.")

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- Popular Destinations Grid ---
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px;">
        <h2 style="font-size: 1.5rem; font-weight: 700; color: #F8FAFC; margin: 0;">🔥 Handpicked Top Destinations</h2>
        <span style="color: #38BDF8; font-size: 0.9rem; font-weight: 600;">Sample Verified Catalog</span>
    </div>
    """, unsafe_allow_html=True)

    featured_dests = fetch_all(
        "SELECT * FROM destinations WHERE is_featured = 1 ORDER BY rating DESC LIMIT 4"
    )
    if not featured_dests:
        featured_dests = fetch_all("SELECT * FROM destinations ORDER BY rating DESC LIMIT 4")

    d_cols = st.columns(len(featured_dests) if featured_dests else 1)
    for idx, d in enumerate(featured_dests):
        with d_cols[idx]:
            img_url = get_image_url(d.get("image_url"), d.get("category", "Heritage"))
            st.markdown(f"""
            <div style="
                background: #1E293B;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin-bottom: 12px;
            ">
                <img src="{img_url}" style="width: 100%; height: 160px; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80';"/>
                <div style="padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.1); padding: 2px 8px; border-radius: 4px;">{d['category']}</span>
                        <span style="font-size: 0.82rem; color: #FBBF24; font-weight: 600;">★ {d['rating']:.1f}</span>
                    </div>
                    <h3 style="font-size: 1.15rem; font-weight: 700; color: #F1F5F9; margin: 0 0 4px 0;">{d['name']}</h3>
                    <p style="font-size: 0.85rem; color: #94A3B8; margin: 0 0 12px 0;">{d['city']}, {d['state_country']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                        <span style="font-size: 0.8rem; color: #64748B;">Estimated:</span>
                        <span style="font-size: 0.95rem; font-weight: 700; color: #34D399;">{format_currency(d['estimated_budget'])}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Explore {d['name']}", key=f"btn_dash_dest_{d['destination_id']}", use_container_width=True):
                st.session_state["nav_selection"] = "Explore Destinations"
                st.session_state["search_destination_filter"] = d["name"]
                st.rerun()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- Featured Vacation Packages ---
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px;">
        <h2 style="font-size: 1.5rem; font-weight: 700; color: #F8FAFC; margin: 0;">✨ Trending Travel Packages</h2>
        <span style="color: #38BDF8; font-size: 0.9rem; font-weight: 600;">All-Inclusive Luxury & Adventure</span>
    </div>
    """, unsafe_allow_html=True)

    featured_pkgs = fetch_all("""
        SELECT p.*, d.name as dest_name, d.state_country
        FROM travel_packages p
        JOIN destinations d ON p.destination_id = d.destination_id
        WHERE p.is_featured = 1
        LIMIT 3
    """)
    if not featured_pkgs:
        featured_pkgs = fetch_all("""
            SELECT p.*, d.name as dest_name, d.state_country
            FROM travel_packages p
            JOIN destinations d ON p.destination_id = d.destination_id
            LIMIT 3
        """)

    pkg_cols = st.columns(len(featured_pkgs) if featured_pkgs else 1)
    for idx, pkg in enumerate(featured_pkgs):
        with pkg_cols[idx]:
            img_url = get_image_url(pkg.get("image_url"), "Package")
            st.markdown(f"""
            <div style="
                background: #1E293B;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin-bottom: 12px;
            ">
                <img src="{img_url}" style="width: 100%; height: 160px; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80';"/>
                <div style="padding: 16px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #10B981; background: rgba(16, 185, 129, 0.1); padding: 2px 8px; border-radius: 4px;">{pkg['package_type']}</span>
                        <span style="font-size: 0.8rem; color: #94A3B8;">⏱️ {pkg['duration_days']}D / {pkg['duration_nights']}N</span>
                    </div>
                    <h3 style="font-size: 1.1rem; font-weight: 700; color: #F1F5F9; margin: 0 0 6px 0; min-height: 48px;">{pkg['title']}</h3>
                    <p style="font-size: 0.82rem; color: #94A3B8; margin: 0 0 10px 0;">📍 {pkg['dest_name']}, {pkg['state_country']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                        <span style="font-size: 0.8rem; color: #64748B;">Starting From</span>
                        <span style="font-size: 1.15rem; font-weight: 800; color: #38BDF8;">{format_currency(pkg['price'])}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"View Package Details", key=f"btn_dash_pkg_{pkg['package_id']}", use_container_width=True):
                st.session_state["nav_selection"] = "Travel Packages"
                st.session_state["selected_package_id"] = pkg["package_id"]
                st.rerun()
