"""
YATRIVO — My Trips & Itinerary Planner Module
User customized trip creation, budget tracking vs actual spent, linked bookings, and itinerary timelines.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import format_currency, format_date, get_status_badge
from auth import get_current_user, is_authenticated


def render_trips():
    user = get_current_user()
    if not is_authenticated() or not user:
        st.warning("🔒 Please log in to manage your trip itineraries.")
        if st.button("Go to Login"):
            st.session_state["nav_selection"] = "Login"
            st.rerun()
        return

    uid = user["user_id"]

    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            🧭 My Trips & Itinerary Planner
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Design personalized vacation plans, track expenses against your budget, and organize multi-day itineraries.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_create = st.tabs(["📋 My Saved Trips", "➕ Create New Trip Plan"])

    # ========================================================
    # TAB 1: SAVED TRIPS & BUDGET PROGRESS
    # ========================================================
    with tab_overview:
        trips = fetch_all("""
            SELECT t.*, d.name as dest_name, d.city, d.state_country
            FROM trips t
            LEFT JOIN destinations d ON t.destination_id = d.destination_id
            WHERE t.user_id = %s
            ORDER BY t.start_date ASC
        """, (uid,))

        if not trips:
            st.info("You don't have any active trip itineraries yet. Click 'Create New Trip Plan' to get started!")
        else:
            for trip in trips:
                tid = trip["trip_id"]
                # Calculate total spent on bookings linked to this trip
                spent_row = fetch_one("""
                    SELECT SUM(total_price) as total_spent
                    FROM bookings
                    WHERE trip_id = %s AND status != 'Cancelled'
                """, (tid,))
                total_spent = float(spent_row["total_spent"]) if (spent_row and spent_row["total_spent"]) else 0.0
                budget = float(trip["budget"])
                pct_used = min(1.0, total_spent / budget) if budget > 0 else 0.0

                badge_html = get_status_badge(trip["status"])

                st.markdown(f"""
                <div style="
                    background: #1E293B;
                    border-radius: 16px;
                    padding: 22px 26px;
                    margin-bottom: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <span style="font-size: 0.8rem; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.12); padding: 3px 10px; border-radius: 4px; text-transform: uppercase;">Trip #{trip['trip_id']}</span>
                            <span style="font-size: 1.35rem; font-weight: 800; color: #F8FAFC; margin-left: 10px;">{trip['title']}</span>
                        </div>
                        <div>{badge_html}</div>
                    </div>
                    <div style="font-size: 0.9rem; color: #CBD5E1; margin-bottom: 12px;">
                        📍 Primary Destination: <b>{trip.get('dest_name', 'Custom Destination')}</b> &bull;
                        🗓️ Dates: <b>{format_date(trip['start_date'])}</b> to <b>{format_date(trip['end_date'])}</b>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 14px; background: rgba(0,0,0,0.2); padding: 10px 14px; border-radius: 8px;">
                        <b>Notes:</b> {trip.get('notes') or 'No notes added yet.'}
                    </div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #94A3B8;">Budget Spent: <b style="color: #38BDF8;">{format_currency(total_spent)}</b> of <b style="color: #F8FAFC;">{format_currency(budget)}</b></span>
                            <span style="color: #34D399; font-weight: 700;">Remaining: {format_currency(max(0, budget - total_spent))}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.progress(pct_used)

                # Show bookings linked to this trip
                linked_bookings = fetch_all("""
                    SELECT * FROM bookings WHERE trip_id = %s
                """, (tid,))

                with st.expander(f"📦 View Linked Bookings & Itinerary for Trip #{tid} ({len(linked_bookings)} items)"):
                    if not linked_bookings:
                        st.caption("No bookings linked to this trip yet. When booking a flight or hotel, choose this trip from the dropdown.")
                    else:
                        for lb in linked_bookings:
                            st.markdown(f"- **{lb['booking_type']}**: {lb['item_title']} ({format_date(lb['travel_start_date'])}) &bull; Cost: `{format_currency(lb['total_price'])}` &bull; Status: `{lb['status']}`")

                    # Option to delete trip
                    del_col, _ = st.columns([1.5, 4])
                    with del_col:
                        if st.button("🗑️ Delete Trip Plan", key=f"del_trip_{tid}"):
                            execute_commit("DELETE FROM trips WHERE trip_id = %s AND user_id = %s", (tid, uid))
                            st.success("Trip plan removed.")
                            st.rerun()

    # ========================================================
    # TAB 2: CREATE NEW TRIP PLAN
    # ========================================================
    with tab_create:
        all_dests = fetch_all("SELECT destination_id, name, city, state_country FROM destinations ORDER BY name")
        d_map = {f"{d['name']} ({d['city']}, {d['state_country']})": d["destination_id"] for d in all_dests}

        with st.form("create_trip_form"):
            st.markdown("### 📝 New Itinerary Details")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                trip_title = st.text_input("Trip Title / Headline", placeholder="e.g. Summer Family Trip to Manali")
                sel_dest_label = st.selectbox("Primary Destination", list(d_map.keys()))
                chosen_did = d_map[sel_dest_label]

            with t_col2:
                trip_budget = st.number_input("Target Budget (₹)", min_value=5000, max_value=1000000, value=50000, step=5000)
                trip_status = st.selectbox("Current Status", ["Planning", "Upcoming", "Completed"])

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                start_d = st.date_input("Start Date", value=datetime.date.today() + datetime.timedelta(days=14))
            with d_col2:
                end_d = st.date_input("End Date", value=datetime.date.today() + datetime.timedelta(days=21))

            trip_notes = st.text_area("Itinerary Notes & Packing Checklist", placeholder="Day 1: Sightseeing, Day 2: Trekking, Day 3: Shopping...")

            submit_trip = st.form_submit_button("Create Trip Itinerary", use_container_width=True)
            if submit_trip:
                if not trip_title.strip():
                    st.error("Please provide a title for your trip.")
                elif end_d < start_d:
                    st.error("End date cannot be earlier than start date.")
                else:
                    insert_trip_query = """
                        INSERT INTO trips (user_id, title, destination_id, start_date, end_date, budget, notes, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    now = datetime.datetime.now()
                    try:
                        new_tid = execute_commit(
                            insert_trip_query,
                            (uid, trip_title.strip(), chosen_did, start_d, end_d, trip_budget, trip_notes, trip_status, now)
                        )
                        # Also link destination
                        execute_commit(
                            "INSERT INTO trip_destinations (trip_id, destination_id, visit_order, stay_days) VALUES (%s, %s, %s, %s)",
                            (new_tid, chosen_did, 1, max(1, (end_d - start_d).days))
                        )
                        st.success(f"🎉 Trip #{new_tid} created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create trip plan: {str(e)}")
