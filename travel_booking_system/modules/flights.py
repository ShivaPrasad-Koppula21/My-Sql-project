"""
YATRIVO — Flight Explorer Module
Flight schedule search, multi-airline filtering, class selection, sorting, and direct booking workflow.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import format_currency, format_datetime, format_duration
from utils.helpers import generate_booking_reference
from auth import get_current_user, is_authenticated


def render_flights():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            ✈️ Flight Explorer
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-bottom: 12px;">
            Compare 500+ commercial flight routes across premier domestic and global airlines.
        </p>
        <div style="background: rgba(56, 189, 248, 0.1); border-left: 4px solid #38BDF8; padding: 10px 16px; border-radius: 6px; font-size: 0.85rem; color: #BAE6FD;">
            ℹ️ <b>Demonstration Dataset:</b> All flight numbers, departure schedules, and seat quotas shown are synthetic demonstration records generated for this academic project.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Fetch available source and destination cities
    all_sources = fetch_all("SELECT DISTINCT source_city FROM flights ORDER BY source_city")
    all_dests = fetch_all("SELECT DISTINCT destination_city FROM flights ORDER BY destination_city")
    all_airlines = fetch_all("SELECT DISTINCT airline FROM flights ORDER BY airline")

    source_cities = ["Any City"] + [r["source_city"] for r in all_sources]
    dest_cities = ["Any City"] + [r["destination_city"] for r in all_dests]
    airline_list = ["All Airlines"] + [r["airline"] for r in all_airlines]

    # --- Search Box ---
    with st.container():
        st.markdown("### 🔍 Search Flight Schedules")
        s1, s2, s3, s4 = st.columns([2, 2, 2, 2])
        with s1:
            sel_src = st.selectbox("🛫 Origin City", source_cities, index=0)
        with s2:
            sel_dest = st.selectbox("🛬 Destination City", dest_cities, index=0)
        with s3:
            dep_date = st.date_input("📅 Departure Date", value=datetime.date.today() + datetime.timedelta(days=7))
        with s4:
            sel_class = st.selectbox("💺 Cabin Class", ["All Classes", "Economy", "Premium Economy", "Business", "First"])

        f1, f2, f3 = st.columns([2, 2, 2])
        with f1:
            sel_airline = st.selectbox("✈️ Airline Filter", airline_list)
        with f2:
            sel_stops = st.selectbox("🛑 Max Stops", ["Any Stops", "Non-stop (0 stops)", "Up to 1 Stop"])
        with f3:
            sort_by = st.selectbox("↕️ Sort Results By", ["Price: Lowest First", "Duration: Shortest First", "Departure: Earliest First"])

    # --- Construct SQL Query ---
    query = "SELECT * FROM flights WHERE 1=1"
    params = []

    if sel_src != "Any City":
        query += " AND source_city = %s"
        params.append(sel_src)
    if sel_dest != "Any City":
        query += " AND destination_city = %s"
        params.append(sel_dest)
    if sel_class != "All Classes":
        query += " AND travel_class = %s"
        params.append(sel_class)
    if sel_airline != "All Airlines":
        query += " AND airline = %s"
        params.append(sel_airline)
    if sel_stops == "Non-stop (0 stops)":
        query += " AND stops = 0"
    elif sel_stops == "Up to 1 Stop":
        query += " AND stops <= 1"

    # Sorting
    if sort_by == "Price: Lowest First":
        query += " ORDER BY price ASC"
    elif sort_by == "Duration: Shortest First":
        query += " ORDER BY duration_minutes ASC"
    elif sort_by == "Departure: Earliest First":
        query += " ORDER BY departure_time ASC"

    query += " LIMIT 50"

    flights = fetch_all(query, tuple(params) if params else None)

    st.markdown(f"<div style='color: #94A3B8; font-size: 0.95rem; margin: 18px 0 14px 0;'>Found <b>{len(flights)}</b> matching flight(s)</div>", unsafe_allow_html=True)

    if not flights:
        st.warning("No flights found matching the selected route or filters. Try selecting 'Any City' or a different airline.")
        return

    # --- Display Flight Cards ---
    for f in flights:
        stops_text = "Direct / Non-stop" if f["stops"] == 0 else f"{f['stops']} Stop(s)"
        stops_badge_color = "#10B981" if f["stops"] == 0 else "#F59E0B"

        st.markdown(f"""
        <div style="
            background: #1E293B;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        ">
            <div style="flex: 2;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <span style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC;">{f['airline']}</span>
                    <span style="background: rgba(255, 255, 255, 0.08); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-family: monospace; color: #38BDF8;">{f['flight_number']}</span>
                    <span style="font-size: 0.78rem; font-weight: 600; color: {stops_badge_color}; background: rgba(0,0,0,0.2); padding: 2px 8px; border-radius: 4px;">{stops_text}</span>
                    <span style="font-size: 0.78rem; color: #CBD5E1; background: rgba(56, 189, 248, 0.15); padding: 2px 8px; border-radius: 4px;">{f['travel_class']}</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 18px; color: #E2E8F0;">
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700;">{f['source_city']}</div>
                        <div style="font-size: 0.82rem; color: #94A3B8;">{format_datetime(f['departure_time'])}</div>
                    </div>
                    <div style="text-align: center; color: #64748B; font-size: 0.82rem; padding: 0 10px;">
                        <div>⏱️ {format_duration(f['duration_minutes'])}</div>
                        <div style="color: #38BDF8;">──────── ✈ ────────</div>
                    </div>
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700;">{f['destination_city']}</div>
                        <div style="font-size: 0.82rem; color: #94A3B8;">{format_datetime(f['arrival_time'])}</div>
                    </div>
                </div>
            </div>
            <div style="flex: 1; text-align: right; border-left: 1px solid rgba(255, 255, 255, 0.08); padding-left: 20px;">
                <div style="font-size: 0.8rem; color: #94A3B8;">Fare per passenger</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #38BDF8; margin-bottom: 4px;">{format_currency(f['price'])}</div>
                <div style="font-size: 0.78rem; color: #10B981; margin-bottom: 10px;">🟢 {f['seats_available']} seats left</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_left, col_btn = st.columns([4, 1])
        with col_btn:
            if st.button("Book This Flight", key=f"book_fl_{f['flight_id']}", use_container_width=True):
                st.session_state["active_booking_flight"] = f
                st.rerun()

    # --- Booking Modal Dialog ---
    active_flight = st.session_state.get("active_booking_flight")
    if active_flight:
        st.markdown("<hr style='border-color: #38BDF8; margin: 24px 0;'/>", unsafe_allow_html=True)
        st.markdown(f"### 🎫 Complete Booking for Flight {active_flight['flight_number']}")

        user = get_current_user()
        if not is_authenticated() or not user:
            st.warning("⚠️ Please log in to complete your flight booking.")
            if st.button("Go to Login"):
                st.session_state["nav_selection"] = "Login"
                st.rerun()
            return

        with st.form("flight_booking_form"):
            b_c1, b_c2 = st.columns(2)
            with b_c1:
                st.markdown(f"**Airline:** {active_flight['airline']}")
                st.markdown(f"**Route:** {active_flight['source_city']} ➔ {active_flight['destination_city']}")
                st.markdown(f"**Departure Time:** {format_datetime(active_flight['departure_time'])}")
                st.markdown(f"**Class:** {active_flight['travel_class']}")

            with b_c2:
                num_passengers = st.number_input("Number of Passengers", min_value=1, max_value=6, value=1)
                unit_fare = float(active_flight["price"])
                total_fare = unit_fare * num_passengers
                st.markdown(f"**Base Fare:** {format_currency(unit_fare)} × {num_passengers}")
                st.markdown(f"### Total Price: {format_currency(total_fare)}")

            passenger_names = st.text_input("Lead Passenger Full Name", value=user["full_name"])
            contact_phone = st.text_input("Contact Phone Number", value=user.get("phone", "+91 98765 00000"))

            # Optional Trip link
            user_trips = fetch_all("SELECT trip_id, title FROM trips WHERE user_id = %s", (user["user_id"],))
            trip_options = {"None (Standalone Booking)": None}
            for tr in user_trips:
                trip_options[f"Trip #{tr['trip_id']}: {tr['title']}"] = tr["trip_id"]

            selected_trip_label = st.selectbox("Link to an existing Trip Plan (Optional)", list(trip_options.keys()))
            linked_trip_id = trip_options[selected_trip_label]

            confirm_submitted = st.form_submit_button("Confirm & Pay Fare", use_container_width=True)

            if confirm_submitted:
                ref = generate_booking_reference("Flight")
                dep_dt = active_flight["departure_time"]
                travel_date = dep_dt.date() if isinstance(dep_dt, datetime.datetime) else datetime.date.today()

                insert_query = """
                    INSERT INTO bookings (
                        booking_reference, user_id, trip_id, booking_type,
                        item_id, item_title, booking_date, travel_start_date, travel_end_date,
                        num_guests, unit_price, total_price, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                title_str = f"{active_flight['airline']} {active_flight['flight_number']} ({active_flight['source_city']} → {active_flight['destination_city']})"
                now = datetime.datetime.now()

                try:
                    execute_commit(
                        insert_query,
                        (ref, user["user_id"], linked_trip_id, "Flight", active_flight["flight_id"],
                         title_str, now, travel_date, travel_date, num_passengers, unit_fare, total_fare,
                         "Confirmed", now)
                    )
                    st.success(f"🎉 Booking Confirmed! Your Booking Reference is **{ref}**.")
                    st.balloons()
                    del st.session_state["active_booking_flight"]
                    st.info("You can review and manage this flight anytime under **My Bookings**.")
                except Exception as e:
                    st.error(f"Failed to record booking: {str(e)}")

        if st.button("Cancel & Return", key="cancel_flight_modal"):
            del st.session_state["active_booking_flight"]
            st.rerun()
