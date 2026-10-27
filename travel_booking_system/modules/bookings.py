"""
YATRIVO — My Bookings Module
Personalized customer booking history, status filters, ticket voucher summaries, and cancellation workflows.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import format_currency, format_date, format_datetime, get_status_badge
from auth import get_current_user, is_authenticated


def render_bookings():
    user = get_current_user()
    if not is_authenticated() or not user:
        st.warning("🔒 You must be logged in to view your bookings.")
        if st.button("Log In Now"):
            st.session_state["nav_selection"] = "Login"
            st.rerun()
        return

    uid = user["user_id"]

    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            📑 My Bookings & Vouchers
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Manage and view your reservations for flights, hotels, tour packages, and guided activities.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Booking Summary Metrics ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    total_cnt = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE user_id = %s", (uid,))
    confirmed_cnt = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE user_id = %s AND status = 'Confirmed'", (uid,))
    completed_cnt = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE user_id = %s AND status = 'Completed'", (uid,))
    cancelled_cnt = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE user_id = %s AND status = 'Cancelled'", (uid,))

    with m_col1:
        st.metric("Total Bookings", total_cnt["cnt"] if total_cnt else 0)
    with m_col2:
        st.metric("Active & Confirmed", confirmed_cnt["cnt"] if confirmed_cnt else 0, delta="Ready to Travel")
    with m_col3:
        st.metric("Completed Trips", completed_cnt["cnt"] if completed_cnt else 0)
    with m_col4:
        st.metric("Cancelled Bookings", cancelled_cnt["cnt"] if cancelled_cnt else 0)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # --- Filters ---
    c_f1, c_f2 = st.columns([2, 2])
    with c_f1:
        status_filter = st.selectbox("Filter by Status", ["All Bookings", "Confirmed", "Completed", "Pending", "Cancelled"])
    with c_f2:
        type_filter = st.selectbox("Filter by Booking Type", ["All Types", "Flight", "Hotel", "Package", "Activity"])

    # Query
    b_query = "SELECT * FROM bookings WHERE user_id = %s"
    b_params = [uid]

    if status_filter != "All Bookings":
        b_query += " AND status = %s"
        b_params.append(status_filter)

    if type_filter != "All Types":
        b_query += " AND booking_type = %s"
        b_params.append(type_filter)

    b_query += " ORDER BY booking_date DESC"
    user_bookings = fetch_all(b_query, tuple(b_params))

    st.markdown(f"<div style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 16px;'>Found <b>{len(user_bookings)}</b> booking records</div>", unsafe_allow_html=True)

    if not user_bookings:
        st.info("No bookings found under the selected filters. Ready to plan your next vacation?")
        if st.button("Explore Destinations"):
            st.session_state["nav_selection"] = "Explore Destinations"
            st.rerun()
        return

    # --- Render Bookings Cards ---
    for b in user_bookings:
        badge_html = get_status_badge(b["status"])
        icon_map = {"Flight": "✈️", "Hotel": "🏨", "Package": "🌴", "Activity": "🚣"}
        icon = icon_map.get(b["booking_type"], "🎫")

        st.markdown(f"""
        <div style="
            background: #1E293B;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.3rem;">{icon}</span>
                    <span style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">{b['booking_type']} Reservation</span>
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38BDF8; font-family: monospace; font-size: 0.85rem; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Ref: {b['booking_reference']}</span>
                </div>
                <div>{badge_html}</div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px;">
                <div>
                    <h3 style="font-size: 1.25rem; font-weight: 700; color: #E2E8F0; margin: 0 0 4px 0;">{b['item_title']}</h3>
                    <div style="font-size: 0.85rem; color: #94A3B8;">
                        🗓️ Travel Dates: <b>{format_date(b['travel_start_date'])}</b> to <b>{format_date(b['travel_end_date'])}</b> &bull; 👥 Guests: <b>{b['num_guests']}</b>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Booked on: {format_datetime(b['booking_date'])}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.8rem; color: #94A3B8;">Total Amount Paid</div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: #34D399;">{format_currency(b['total_price'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action Buttons: Cancel Booking or View Receipt
        if b["status"] in ["Confirmed", "Pending"]:
            b_act1, b_act2, _ = st.columns([1.5, 1.5, 3])
            with b_act1:
                if st.button("❌ Cancel Reservation", key=f"cancel_btn_{b['booking_id']}"):
                    st.session_state["target_cancel_booking"] = b
                    st.rerun()

    # --- Cancellation Modal Dialog ---
    cancel_target = st.session_state.get("target_cancel_booking")
    if cancel_target:
        st.markdown("<hr style='border-color: #EF4444; margin: 24px 0;'/>", unsafe_allow_html=True)
        st.markdown(f"### ⚠️ Confirm Cancellation for Booking `{cancel_target['booking_reference']}`")
        st.markdown(f"**Item:** {cancel_target['item_title']} ({cancel_target['booking_type']})")
        st.markdown(f"**Paid Amount:** `{format_currency(cancel_target['total_price'])}`")

        with st.form("cancel_confirm_form"):
            reason = st.text_area("Please provide a cancellation reason (Required for refund processing):", placeholder="e.g. Change of flight dates, medical emergency...")
            confirm_cancel = st.form_submit_button("Proceed with Cancellation", use_container_width=True)

            if confirm_cancel:
                if not reason.strip():
                    st.error("Please provide a brief reason for cancellation.")
                else:
                    upd_query = "UPDATE bookings SET status = 'Cancelled', cancellation_reason = %s WHERE booking_id = %s AND user_id = %s"
                    try:
                        execute_commit(upd_query, (reason.strip(), cancel_target["booking_id"], uid))
                        st.success("Booking cancelled successfully. Your refund request has been initiated.")
                        del st.session_state["target_cancel_booking"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to cancel booking: {str(e)}")

        if st.button("Abandon Cancellation", key="abandon_cancel"):
            del st.session_state["target_cancel_booking"]
            st.rerun()
