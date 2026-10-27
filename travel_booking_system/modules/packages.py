"""
YATRIVO — Travel Packages & Activities Module
Curated all-inclusive vacations, day excursions, outdoor adventure sports, and instant booking workflows.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import format_currency
from utils.helpers import get_image_url, generate_booking_reference, truncate_text
from auth import get_current_user, is_authenticated


def render_packages():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            🎒 Curated Packages & Activities
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Explore 100+ all-inclusive holiday itineraries and 200+ thrilling guided excursions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_packages, tab_activities = st.tabs(["🌴 Vacation Packages (100+)", "🚣 Activities & Excursions (200+)"])

    # ========================================================
    # TAB 1: VACATION PACKAGES
    # ========================================================
    with tab_packages:
        p_c1, p_c2, p_c3 = st.columns([3, 2, 2])
        with p_c1:
            pkg_type_opt = st.selectbox("Package Category", ["All Categories", "Domestic", "International", "Honeymoon", "Adventure", "Family", "Solo"])
        with p_c2:
            max_pkg_price = st.slider("Max Package Budget (₹)", min_value=15000, max_value=250000, value=200000, step=5000)
        with p_c3:
            pkg_sort = st.selectbox("Sort Packages", ["Price: Low to High", "Price: High to Low", "Duration: Longest", "Duration: Shortest"])

        # Query
        p_query = """
            SELECT p.*, d.name as dest_name, d.state_country
            FROM travel_packages p
            JOIN destinations d ON p.destination_id = d.destination_id
            WHERE p.price <= %s
        """
        p_params = [max_pkg_price]
        if pkg_type_opt != "All Categories":
            p_query += " AND p.package_type = %s"
            p_params.append(pkg_type_opt)

        if pkg_sort == "Price: Low to High":
            p_query += " ORDER BY p.price ASC"
        elif pkg_sort == "Price: High to Low":
            p_query += " ORDER BY p.price DESC"
        elif pkg_sort == "Duration: Longest":
            p_query += " ORDER BY p.duration_days DESC"
        else:
            p_query += " ORDER BY p.duration_days ASC"

        packages = fetch_all(p_query, tuple(p_params))
        st.markdown(f"<div style='color: #94A3B8; font-size: 0.92rem; margin: 12px 0 16px 0;'>Showing <b>{len(packages)}</b> packages</div>", unsafe_allow_html=True)

        # Grid of packages (2 per row)
        for i in range(0, len(packages[:24]), 2):
            row_pkgs = packages[i:i + 2]
            cols = st.columns(2)
            for c_idx, pkg in enumerate(row_pkgs):
                with cols[c_idx]:
                    img_url = get_image_url(pkg.get("image_url"), "Package")
                    st.markdown(f"""
                    <div style="
                        background: #1E293B;
                        border-radius: 16px;
                        overflow: hidden;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        margin-bottom: 16px;
                    ">
                        <img src="{img_url}" style="width: 100%; height: 180px; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80';"/>
                        <div style="padding: 18px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #10B981; background: rgba(16, 185, 129, 0.12); padding: 3px 8px; border-radius: 4px;">{pkg['package_type']}</span>
                                <span style="font-size: 0.82rem; color: #38BDF8; font-weight: 600;">⏱️ {pkg['duration_days']} Days / {pkg['duration_nights']} Nights</span>
                            </div>
                            <h3 style="font-size: 1.2rem; font-weight: 700; color: #F8FAFC; margin: 0 0 4px 0;">{pkg['title']}</h3>
                            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 8px;">📍 Destination: <b>{pkg['dest_name']}, {pkg['state_country']}</b></div>
                            <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.4; margin-bottom: 10px; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 8px;">
                                <b>Included:</b> {pkg['inclusions']}
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: baseline; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px;">
                                <span style="font-size: 0.8rem; color: #94A3B8;">Starting Package Cost</span>
                                <span style="font-size: 1.35rem; font-weight: 800; color: #38BDF8;">{format_currency(pkg['price'])}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Book Package #{pkg['package_id']}", key=f"btn_pkg_book_{pkg['package_id']}", use_container_width=True):
                        st.session_state["active_booking_pkg"] = pkg
                        st.rerun()

    # ========================================================
    # TAB 2: ACTIVITIES & EXCURSIONS
    # ========================================================
    with tab_activities:
        a_c1, a_c2 = st.columns([3, 2])
        with a_c1:
            act_cat = st.selectbox("Activity Theme", ["All Themes", "Water Sports", "Sightseeing", "Trekking", "Cultural", "Culinary", "Safari", "Adventure"])
        with a_c2:
            max_act_price = st.slider("Max Activity Price (₹)", min_value=500, max_value=15000, value=10000, step=500)

        act_query = """
            SELECT a.*, d.name as dest_name
            FROM activities a
            JOIN destinations d ON a.destination_id = d.destination_id
            WHERE a.price <= %s
        """
        act_params = [max_act_price]
        if act_cat != "All Themes":
            act_query += " AND a.category = %s"
            act_params.append(act_cat)

        act_query += " ORDER BY a.price ASC LIMIT 30"
        activities = fetch_all(act_query, tuple(act_params))

        st.markdown(f"<div style='color: #94A3B8; font-size: 0.92rem; margin: 12px 0 16px 0;'>Showing <b>{len(activities)}</b> outdoor experiences</div>", unsafe_allow_html=True)

        for act in activities:
            img_url = get_image_url(act.get("image_url"), act["category"])
            st.markdown(f"""
            <div style="
                background: #1E293B;
                border-radius: 14px;
                padding: 16px 20px;
                margin-bottom: 14px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="display: flex; gap: 16px; align-items: center;">
                    <img src="{img_url}" style="width: 80px; height: 80px; border-radius: 10px; object-fit: cover;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1527631746610-bca00a040d60?auto=format&fit=crop&w=800&q=80';"/>
                    <div>
                        <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #F59E0B; background: rgba(245, 158, 11, 0.12); padding: 2px 8px; border-radius: 4px;">{act['category']}</span>
                        <h4 style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 2px 0;">{act['title']}</h4>
                        <div style="font-size: 0.82rem; color: #94A3B8;">📍 Location: {act['location']} ({act['dest_name']}) &bull; ⏱️ Duration: {act['duration_hours']} Hours</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #34D399; margin-bottom: 6px;">{format_currency(act['price'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            _, btn_act_col = st.columns([4, 1])
            with btn_act_col:
                if st.button("Book Activity", key=f"btn_act_{act['activity_id']}", use_container_width=True):
                    st.session_state["active_booking_act"] = act
                    st.rerun()

    # --- Booking Dialog for Package ---
    active_pkg = st.session_state.get("active_booking_pkg")
    if active_pkg:
        st.markdown("<hr style='border-color: #38BDF8; margin: 28px 0;'/>", unsafe_allow_html=True)
        st.markdown(f"### 🌴 Book Vacation Package: {active_pkg['title']}")

        user = get_current_user()
        if not is_authenticated() or not user:
            st.warning("⚠️ Please log in to complete your package booking.")
            if st.button("Go to Login", key="login_pkg"):
                st.session_state["nav_selection"] = "Login"
                st.rerun()
            return

        with st.form("package_booking_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Destination:** {active_pkg['dest_name']}")
                st.markdown(f"**Duration:** {active_pkg['duration_days']} Days / {active_pkg['duration_nights']} Nights")
                st.markdown(f"**Itinerary Overview:**\n\n{active_pkg['itinerary_summary']}")
            with c2:
                travel_date = st.date_input("Select Vacation Start Date", value=datetime.date.today() + datetime.timedelta(days=14))
                guests = st.number_input("Number of Travelers", min_value=1, max_value=20, value=2)
                unit_price = float(active_pkg["price"])
                total_cost = unit_price * guests
                st.markdown(f"### Total Package Price: {format_currency(total_cost)}")

            pkg_submit = st.form_submit_button("Confirm Package Booking", use_container_width=True)
            if pkg_submit:
                ref = generate_booking_reference("Package")
                end_travel_date = travel_date + datetime.timedelta(days=int(active_pkg["duration_days"]))
                now = datetime.datetime.now()

                query = """
                    INSERT INTO bookings (
                        booking_reference, user_id, booking_type, item_id, item_title,
                        booking_date, travel_start_date, travel_end_date, num_guests, unit_price, total_price, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                try:
                    execute_commit(
                        query,
                        (ref, user["user_id"], "Package", active_pkg["package_id"], active_pkg["title"],
                         now, travel_date, end_travel_date, guests, unit_price, total_cost, "Confirmed", now)
                    )
                    st.success(f"🎉 Package Booking Confirmed! Reference: **{ref}**.")
                    st.balloons()
                    del st.session_state["active_booking_pkg"]
                except Exception as e:
                    st.error(f"Error booking package: {str(e)}")

        if st.button("Cancel & Return", key="cancel_pkg_modal"):
            del st.session_state["active_booking_pkg"]
            st.rerun()

    # --- Booking Dialog for Activity ---
    active_act = st.session_state.get("active_booking_act")
    if active_act:
        st.markdown("<hr style='border-color: #38BDF8; margin: 28px 0;'/>", unsafe_allow_html=True)
        st.markdown(f"### 🚣 Reserve Activity: {active_act['title']}")

        user = get_current_user()
        if not is_authenticated() or not user:
            st.warning("⚠️ Please log in to complete your activity booking.")
            return

        with st.form("act_booking_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Location:** {active_act['location']} ({active_act['dest_name']})")
                st.markdown(f"**Duration:** {active_act['duration_hours']} Hours")
            with c2:
                act_date = st.date_input("Activity Date", value=datetime.date.today() + datetime.timedelta(days=7))
                act_guests = st.number_input("Participants", min_value=1, max_value=10, value=2)
                act_unit = float(active_act["price"])
                act_total = act_unit * act_guests
                st.markdown(f"### Total Price: {format_currency(act_total)}")

            if st.form_submit_button("Confirm Activity Reservation", use_container_width=True):
                ref = generate_booking_reference("Activity")
                now = datetime.datetime.now()
                query = """
                    INSERT INTO bookings (
                        booking_reference, user_id, booking_type, item_id, item_title,
                        booking_date, travel_start_date, travel_end_date, num_guests, unit_price, total_price, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                try:
                    execute_commit(
                        query,
                        (ref, user["user_id"], "Activity", active_act["activity_id"], active_act["title"],
                         now, act_date, act_date, act_guests, act_unit, act_total, "Confirmed", now)
                    )
                    st.success(f"🎉 Activity Reserved! Reference: **{ref}**.")
                    st.balloons()
                    del st.session_state["active_booking_act"]
                except Exception as e:
                    st.error(f"Error booking activity: {str(e)}")

        if st.button("Cancel & Return", key="cancel_act_modal"):
            del st.session_state["active_booking_act"]
            st.rerun()
