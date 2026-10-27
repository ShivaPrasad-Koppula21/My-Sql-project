"""
YATRIVO — Hotel Explorer Module
Hotel search, amenities filtering, star ratings, stay duration calculation, and booking engine.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import format_currency, render_stars
from utils.helpers import get_image_url, calculate_stay_nights, generate_booking_reference, truncate_text
from auth import get_current_user, is_authenticated


def render_hotels():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            🏨 Hotel Explorer & Luxury Stays
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Discover 150+ verified luxury resorts, heritage villas, and boutique hotels across premier travel destinations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch destinations for filter
    all_dests = fetch_all("SELECT destination_id, name, city, state_country FROM destinations ORDER BY name")
    dest_options = {"All Destinations": None}
    dest_id_to_index = {"All Destinations": 0}
    for idx, d in enumerate(all_dests, start=1):
        label = f"{d['name']} ({d['city']}, {d['state_country']})"
        dest_options[label] = d["destination_id"]
        dest_id_to_index[d["destination_id"]] = idx

    default_dest_idx = 0
    if "hotel_dest_filter" in st.session_state:
        target_did = st.session_state.pop("hotel_dest_filter")
        default_dest_idx = dest_id_to_index.get(target_did, 0)

    # --- Search & Date Filters ---
    with st.container():
        st.markdown("### 🔍 Search Stays & Dates")
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

        with c1:
            sel_dest_label = st.selectbox("📍 Destination", list(dest_options.keys()), index=default_dest_idx)
            selected_dest_id = dest_options[sel_dest_label]

        with c2:
            check_in = st.date_input("📅 Check-in Date", value=datetime.date.today() + datetime.timedelta(days=7))

        with c3:
            check_out = st.date_input("📅 Check-out Date", value=datetime.date.today() + datetime.timedelta(days=10))

        with c4:
            star_filter = st.selectbox("⭐ Minimum Stars", ["Any Stars", "5 Stars Luxury", "4+ Stars", "3+ Stars"])

        # Row 2: Property Type, Max Price, Amenity
        r1, r2, r3 = st.columns([2, 2, 2])
        with r1:
            prop_type_opts = ["All Property Types", "Luxury Resort", "Boutique Hotel", "Business Hotel", "Heritage Villa", "Budget Hotel"]
            sel_prop_type = st.selectbox("🏰 Property Type", prop_type_opts)
        with r2:
            max_price = st.slider("💰 Max Price Per Night (₹)", min_value=2000, max_value=40000, value=35000, step=1000)
        with r3:
            amenity_opt = st.selectbox("✨ Featured Amenity", ["All Amenities", "Swimming Pool", "Spa", "Ocean View", "Free Wi-Fi", "Airport Shuttle"])

    # Calculate Nights
    nights = calculate_stay_nights(check_in, check_out)
    st.markdown(f"<div style='color: #38BDF8; font-weight: 600; margin: 10px 0;'>Stay Duration: <b>{nights} night(s)</b> ({check_in.strftime('%d %b')} to {check_out.strftime('%d %b %Y')})</div>", unsafe_allow_html=True)

    # --- SQL Query ---
    query = """
        SELECT h.*, d.name as dest_name, d.state_country
        FROM hotels h
        JOIN destinations d ON h.destination_id = d.destination_id
        WHERE h.price_per_night <= %s
    """
    params = [max_price]

    if selected_dest_id:
        query += " AND h.destination_id = %s"
        params.append(selected_dest_id)

    if star_filter == "5 Stars Luxury":
        query += " AND h.star_rating = 5"
    elif star_filter == "4+ Stars":
        query += " AND h.star_rating >= 4"
    elif star_filter == "3+ Stars":
        query += " AND h.star_rating >= 3"

    if sel_prop_type != "All Property Types":
        query += " AND h.property_type = %s"
        params.append(sel_prop_type)

    if amenity_opt != "All Amenities":
        query += " AND LOWER(h.amenities) LIKE %s"
        params.append(f"%{amenity_opt.lower()}%")

    query += " ORDER BY h.star_rating DESC, h.price_per_night ASC LIMIT 30"

    hotels = fetch_all(query, tuple(params))

    st.markdown(f"<div style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 16px;'>Showing <b>{len(hotels)}</b> available hotel property(s)</div>", unsafe_allow_html=True)

    if not hotels:
        st.info("No hotels matched your selected criteria. Try adjusting the budget slider or selecting 'All Destinations'.")
        return

    # --- Hotel Cards ---
    for h in hotels:
        img_url = get_image_url(h.get("image_url"), "Hotel")
        est_stay_cost = float(h["price_per_night"]) * nights

        st.markdown(f"""
        <div style="
            background: #1E293B;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 20px;
            display: flex;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        ">
            <div style="width: 280px; min-width: 280px; position: relative;">
                <img src="{img_url}" style="width: 100%; height: 100%; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80';"/>
            </div>
            <div style="padding: 20px 24px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.12); padding: 3px 8px; border-radius: 4px;">{h['property_type']}</span>
                        <span style="color: #FBBF24; font-size: 0.95rem; font-weight: 700;">{render_stars(h['star_rating'])} ({h['star_rating']} Stars)</span>
                    </div>
                    <h3 style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; margin: 0 0 4px 0;">{h['name']}</h3>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 10px;">📍 {h['address']}, {h['dest_name']}</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5; margin-bottom: 12px;">
                        <b>Amenities:</b> {truncate_text(h['amenities'], 140)}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 12px;">
                    <div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Price per night</div>
                        <div style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC;">{format_currency(h['price_per_night'])}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.82rem; color: #64748B;">Total for {nights} Night(s)</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #34D399; margin-bottom: 6px;">{format_currency(est_stay_cost)}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        _, book_col = st.columns([4, 1])
        with book_col:
            if st.button(f"Select & Book Stay", key=f"btn_hotel_{h['hotel_id']}", use_container_width=True):
                st.session_state["active_booking_hotel"] = h
                st.session_state["booking_checkin"] = check_in
                st.session_state["booking_checkout"] = check_out
                st.session_state["booking_nights"] = nights
                st.rerun()

    # --- Booking Modal Dialog ---
    active_hotel = st.session_state.get("active_booking_hotel")
    if active_hotel:
        st.markdown("<hr style='border-color: #38BDF8; margin: 28px 0;'/>", unsafe_allow_html=True)
        st.markdown(f"### 🏨 Book Room at {active_hotel['name']}")

        user = get_current_user()
        if not is_authenticated() or not user:
            st.warning("⚠️ Please log in to complete your hotel booking.")
            if st.button("Go to Login"):
                st.session_state["nav_selection"] = "Login"
                st.rerun()
            return

        # Fetch room types for this hotel
        rooms = fetch_all("SELECT * FROM hotel_rooms WHERE hotel_id = %s", (active_hotel["hotel_id"],))
        room_options = {}
        for r in rooms:
            room_options[f"{r['room_type']} (Cap: {r['capacity']} Guests) — {format_currency(r['price_per_night'])}/night"] = r

        if not room_options:
            room_options["Standard Suite — " + format_currency(active_hotel["price_per_night"]) + "/night"] = {
                "room_id": 0, "room_type": "Standard Suite", "price_per_night": active_hotel["price_per_night"]
            }

        with st.form("hotel_booking_form"):
            hb1, hb2 = st.columns(2)
            with hb1:
                st.markdown(f"**Hotel:** {active_hotel['name']}")
                st.markdown(f"**Location:** {active_hotel['address']}, {active_hotel['dest_name']}")
                st.markdown(f"**Dates:** {st.session_state['booking_checkin'].strftime('%d %b %Y')} to {st.session_state['booking_checkout'].strftime('%d %b %Y')}")
                st.markdown(f"**Duration:** {st.session_state['booking_nights']} Night(s)")

            with hb2:
                selected_room_label = st.selectbox("Select Room Category", list(room_options.keys()))
                chosen_room = room_options[selected_room_label]
                num_rooms = st.number_input("Number of Rooms", min_value=1, max_value=5, value=1)
                num_guests = st.number_input("Total Guests", min_value=1, max_value=10, value=2)

                unit_price = float(chosen_room["price_per_night"])
                total_stay_cost = unit_price * st.session_state["booking_nights"] * num_rooms
                st.markdown(f"### Total Stay Cost: {format_currency(total_stay_cost)}")

            # Trip plan link
            user_trips = fetch_all("SELECT trip_id, title FROM trips WHERE user_id = %s", (user["user_id"],))
            trip_options = {"None (Standalone Booking)": None}
            for tr in user_trips:
                trip_options[f"Trip #{tr['trip_id']}: {tr['title']}"] = tr["trip_id"]
            selected_trip = st.selectbox("Link to Trip Plan (Optional)", list(trip_options.keys()))
            linked_trip_id = trip_options[selected_trip]

            hotel_confirm = st.form_submit_button("Confirm Hotel Reservation", use_container_width=True)

            if hotel_confirm:
                ref = generate_booking_reference("Hotel")
                title_str = f"{active_hotel['name']} ({chosen_room['room_type']})"
                now = datetime.datetime.now()

                insert_query = """
                    INSERT INTO bookings (
                        booking_reference, user_id, trip_id, booking_type,
                        item_id, item_title, booking_date, travel_start_date, travel_end_date,
                        num_guests, unit_price, total_price, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                try:
                    execute_commit(
                        insert_query,
                        (ref, user["user_id"], linked_trip_id, "Hotel", active_hotel["hotel_id"],
                         title_str, now, st.session_state["booking_checkin"], st.session_state["booking_checkout"],
                         num_guests, unit_price, total_stay_cost, "Confirmed", now)
                    )
                    st.success(f"🎉 Hotel Booking Confirmed! Reference: **{ref}**.")
                    st.balloons()
                    del st.session_state["active_booking_hotel"]
                    st.info("You can view your confirmed stay voucher in **My Bookings**.")
                except Exception as e:
                    st.error(f"Failed to save hotel reservation: {str(e)}")

        if st.button("Cancel & Return", key="cancel_hotel_modal"):
            del st.session_state["active_booking_hotel"]
            st.rerun()
