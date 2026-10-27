"""
====================================================================
YATRIVO — Administrator Control Center & Security Operations Module
Role-gated administration dashboard, two-stage administrator enrollment
approval workflow, catalog CRUD, interactive Plotly charts, and system diagnostics.
====================================================================
"""

import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import fetch_all, fetch_one, execute_commit, get_table_counts
from utils.formatting import format_currency, format_datetime, get_status_badge
from utils.helpers import get_image_url
from auth import (
    is_admin,
    get_current_user,
    get_admin_enrollment_requests,
    approve_admin_request,
    reject_admin_request
)


def render_admin():
    if not is_admin():
        st.error("⛔ Access Denied: Administrator credentials required to access this control panel.")
        return

    admin_user = get_current_user()
    admin_id = admin_user["user_id"] if admin_user else 1

    st.markdown("""
    <div style="margin-bottom: 24px;">
        <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 14px; border-radius: 9999px; background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; color: #F87171; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;">
            <span>🛡️</span> <span>Yatrivo Enterprise Security & Control Portal</span>
        </div>
        <h1 style="color: #F8FAFC; font-size: 2.3rem; font-weight: 800; margin: 0 0 6px 0;">
            System Administration & Control Center
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin: 0;">
            Enterprise oversight: administrator authorization workflow, live catalog CRUD, booking moderation, and database operations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Top KPI Metric Cards ---
    total_rev_row = fetch_one("SELECT SUM(total_price) as rev FROM bookings WHERE status != 'Cancelled'")
    total_rev = float(total_rev_row["rev"]) if (total_rev_row and total_rev_row["rev"]) else 0.0

    total_bk_row = fetch_one("SELECT COUNT(*) as cnt FROM bookings")
    cancel_bk_row = fetch_one("SELECT COUNT(*) as cnt FROM bookings WHERE status = 'Cancelled'")
    cust_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM users WHERE role = 'customer'")
    admin_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin' AND account_status = 'active'")
    pending_admin_row = fetch_one("SELECT COUNT(*) as cnt FROM admin_enrollment_requests WHERE status = 'pending'")
    pending_admins = pending_admin_row["cnt"] if pending_admin_row else 0

    dest_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM destinations")
    flight_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM flights")
    hotel_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM hotels")
    pkg_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM travel_packages")
    act_cnt_row = fetch_one("SELECT COUNT(*) as cnt FROM activities")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Booking Revenue", format_currency(total_rev), delta="Confirmed Sales")
    with k2:
        st.metric("Total Bookings", total_bk_row["cnt"] if total_bk_row else 0, delta=f"{cancel_bk_row['cnt'] if cancel_bk_row else 0} Cancelled")
    with k3:
        st.metric("Registered Customers", cust_cnt_row["cnt"] if cust_cnt_row else 0, delta="Active Travelers")
    with k4:
        st.metric("Pending Admin Requests", pending_admins, delta="Action Needed" if pending_admins > 0 else "All Clean")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Secondary Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Active Destinations", dest_cnt_row["cnt"] if dest_cnt_row else 60)
    with m2:
        st.metric("Available Flights", flight_cnt_row["cnt"] if flight_cnt_row else 500)
    with m3:
        st.metric("Hotels & Resorts", hotel_cnt_row["cnt"] if hotel_cnt_row else 150)
    with m4:
        st.metric("Packages & Activities", (pkg_cnt_row["cnt"] if pkg_cnt_row else 100) + (act_cnt_row["cnt"] if act_cnt_row else 200))

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- Pending Administrator Notification Banner ---
    if pending_admins > 0:
        st.warning(
            f"🔔 **Security Action Required:** There are **{pending_admins}** pending administrator enrollment requests awaiting your authorization. Review them under the **'🛡️ Admin Enrollment Approvals'** tab below."
        )

    # --- Admin Tabs ---
    tab_approval, tab_analytics, tab_dest, tab_flights, tab_hotels, tab_bookings, tab_reviews, tab_system = st.tabs([
        f"🛡️ Admin Approvals ({pending_admins})",
        "📈 Executive Analytics",
        "🗺️ Destinations CRUD",
        "✈️ Flights CRUD",
        "🏨 Hotels CRUD",
        "📑 Bookings Manager",
        "⭐ Review Moderation",
        "⚙️ Database & Stats"
    ])

    # ========================================================
    # 1. ADMINISTRATOR ENROLLMENT APPROVAL WORKFLOW
    # ========================================================
    with tab_approval:
        st.subheader("🛡️ Administrator Enrollment Requests & Access Control")
        st.caption("Review privileged administrator account requests submitted with valid invitation tokens.")

        req_subtab1, req_subtab2 = st.tabs(["⏳ Pending Approvals", "📜 Enrollment History"])

        with req_subtab1:
            pending_reqs = get_admin_enrollment_requests("pending")
            if not pending_reqs:
                st.success("✅ No pending administrator enrollment requests. All account queues are clear.")
            else:
                st.markdown(f"**{len(pending_reqs)} Pending Request(s) Awaiting Review:**")
                for req in pending_reqs:
                    st.markdown(f"""
                    <div style="background: #1E293B; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">👤 {req['full_name']}</span>
                            <span style="font-size: 0.78rem; background: rgba(239, 68, 68, 0.2); color: #F87171; padding: 3px 10px; border-radius: 9999px; font-weight: 600;">PENDING REVIEW</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #CBD5E1; margin-bottom: 4px;">
                            <b>Email:</b> <code>{req['email']}</code> &bull; <b>Phone:</b> {req.get('phone') or 'Not provided'}
                        </div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">
                            <b>Request Submitted:</b> {format_datetime(req['requested_at'])} &bull; <b>Token Verified:</b> Server Secret Code Matched
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_c1, btn_c2, _ = st.columns([1.5, 1.5, 4])
                    with btn_c1:
                        if st.button("✅ Approve Administrator", key=f"appr_req_{req['request_id']}", use_container_width=True):
                            ok, msg = approve_admin_request(req["request_id"], admin_id)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with btn_c2:
                        if st.button("❌ Reject Request", key=f"rej_req_{req['request_id']}", use_container_width=True):
                            ok, msg = reject_admin_request(req["request_id"], admin_id, "Declined by system administrator")
                            if ok:
                                st.warning(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        with req_subtab2:
            st.markdown("#### Historical Enrollment Audit Log")
            hist_query = """
                SELECT r.request_id, u.full_name, u.email, r.status, r.requested_at, r.reviewed_at, r.rejection_reason,
                       rev.full_name as reviewer_name
                FROM admin_enrollment_requests r
                JOIN users u ON r.user_id = u.user_id
                LEFT JOIN users rev ON r.reviewed_by = rev.user_id
                WHERE r.status IN ('approved', 'rejected')
                ORDER BY r.reviewed_at DESC LIMIT 20
            """
            hist_data = fetch_all(hist_query)
            if hist_data:
                df_hist = pd.DataFrame(hist_data)
                df_hist.columns = ["ID", "Applicant", "Email", "Status", "Requested At", "Reviewed At", "Notes", "Reviewer"]
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("No completed enrollment decisions in audit history yet.")

    # ========================================================
    # 2. EXECUTIVE ANALYTICS CHARTS
    # ========================================================
    with tab_analytics:
        st.subheader("📈 Interactive Business Analytics & Booking Trends")

        # Booking trends over time
        b_trend = fetch_all("""
            SELECT DATE(booking_date) as b_date, COUNT(*) as bookings_count, SUM(total_price) as daily_revenue
            FROM bookings
            WHERE status != 'Cancelled'
            GROUP BY DATE(booking_date)
            ORDER BY b_date ASC LIMIT 60
        """)
        if b_trend:
            df_trend = pd.DataFrame(b_trend)
            df_trend["b_date"] = pd.to_datetime(df_trend["b_date"])
            fig_trend = px.line(
                df_trend,
                x="b_date",
                y="daily_revenue",
                title="Daily Booking Revenue Trends (₹)",
                labels={"b_date": "Date", "daily_revenue": "Revenue (₹)"},
                template="plotly_dark"
            )
            fig_trend.update_traces(line_color="#06B6D4", line_width=3)
            fig_trend.update_layout(paper_bgcolor="#0F172A", plot_bgcolor="#1E293B")
            st.plotly_chart(fig_trend, use_container_width=True)

        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            # Revenue by Category
            cat_rev = fetch_all("""
                SELECT booking_type, SUM(total_price) as revenue
                FROM bookings
                WHERE status != 'Cancelled'
                GROUP BY booking_type
            """)
            if cat_rev:
                df_cat = pd.DataFrame(cat_rev)
                fig_cat = px.pie(
                    df_cat,
                    values="revenue",
                    names="booking_type",
                    title="Revenue Breakdown by Category",
                    hole=0.45,
                    color_discrete_sequence=["#06B6D4", "#10B981", "#F59E0B", "#8B5CF6"],
                    template="plotly_dark"
                )
                fig_cat.update_layout(paper_bgcolor="#0F172A")
                st.plotly_chart(fig_cat, use_container_width=True)

        with chart_c2:
            # Booking Status Distribution
            st_counts = fetch_all("SELECT status, COUNT(*) as count FROM bookings GROUP BY status")
            if st_counts:
                df_st = pd.DataFrame(st_counts)
                fig_st = px.bar(
                    df_st,
                    x="status",
                    y="count",
                    title="Booking Status Distribution",
                    color="status",
                    color_discrete_map={
                        "Confirmed": "#10B981",
                        "Completed": "#06B6D4",
                        "Cancelled": "#EF4444",
                        "Pending": "#F59E0B"
                    },
                    template="plotly_dark"
                )
                fig_st.update_layout(paper_bgcolor="#0F172A", plot_bgcolor="#1E293B", showlegend=False)
                st.plotly_chart(fig_st, use_container_width=True)

    # ========================================================
    # 3. DESTINATIONS CRUD
    # ========================================================
    with tab_dest:
        st.subheader("Manage Destination Catalog")
        dest_action = st.radio("Destination Action", ["View All / Search", "Add New Destination"], horizontal=True)

        if dest_action == "Add New Destination":
            with st.form("add_destination_form"):
                d_name = st.text_input("Destination Name (e.g., Shimla, Tokyo)")
                d_city = st.text_input("City")
                d_state = st.text_input("State / Country (e.g., India, France)")
                d_cat = st.selectbox("Category", ["Beach", "Mountain", "Heritage", "Urban", "Wildlife", "Adventure", "Island", "Spiritual"])
                d_desc = st.text_area("Overview & Highlights")
                d_btime = st.text_input("Best Time to Visit", value="Oct - Mar")
                d_budget = st.number_input("Estimated Budget (₹)", min_value=1000, max_value=500000, value=25000, step=1000)
                d_img = st.text_input("Image URL (Unsplash or direct image link)")
                d_feat = st.checkbox("Feature on Customer Dashboard")

                if st.form_submit_button("Create Destination", use_container_width=True):
                    if not d_name.strip() or not d_city.strip() or not d_state.strip():
                        st.error("Name, city, and state/country are required.")
                    else:
                        img_to_use = d_img.strip() if d_img.strip() else get_image_url("", d_cat)
                        query = """
                            INSERT INTO destinations (name, city, state_country, category, description, best_time_to_visit, estimated_budget, image_url, rating, is_featured, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        try:
                            execute_commit(query, (d_name.strip(), d_city.strip(), d_state.strip(), d_cat, d_desc.strip(), d_btime.strip(), d_budget, img_to_use, 4.5, 1 if d_feat else 0, datetime.datetime.now()))
                            st.success(f"Destination '{d_name}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding destination: {str(e)}")

        else:
            search_d = st.text_input("Filter Destination by Name", placeholder="Type destination name...")
            q = "SELECT * FROM destinations"
            p = []
            if search_d:
                q += " WHERE name LIKE %s OR city LIKE %s"
                p = [f"%{search_d}%", f"%{search_d}%"]
            q += " ORDER BY destination_id DESC LIMIT 30"
            dest_list = fetch_all(q, tuple(p) if p else None)

            st.caption(f"Showing {len(dest_list)} destinations:")
            for d in dest_list:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{d['name']}** &bull; {d['city']}, {d['state_country']} &bull; `{d['category']}` &bull; Budget: `{format_currency(d['estimated_budget'])}` &bull; Rating: {d['rating']}★")
                with c2:
                    if st.button("🗑️ Delete", key=f"del_dest_{d['destination_id']}"):
                        execute_commit("DELETE FROM destinations WHERE destination_id = %s", (d["destination_id"],))
                        st.warning(f"Destination #{d['destination_id']} removed.")
                        st.rerun()

    # ========================================================
    # 4. FLIGHTS CRUD
    # ========================================================
    with tab_flights:
        st.subheader("Manage Flights Catalog")
        flight_action = st.radio("Flight Action", ["View All / Filter", "Add New Flight"], horizontal=True)

        if flight_action == "Add New Flight":
            with st.form("add_flight_form"):
                f_num = st.text_input("Flight Number (e.g. 6E-505, AI-801)")
                f_air = st.selectbox("Airline", ["IndiGo", "Air India", "Vistara", "Akasa Air", "SpiceJet", "Emirates", "Qatar Airways", "Singapore Airlines"])
                c_src, c_dst = st.columns(2)
                with c_src:
                    f_src = st.text_input("Source City (e.g. Delhi)")
                with c_dst:
                    f_dst = st.text_input("Destination City (e.g. Goa)")
                f_price = st.number_input("Base Price (₹)", min_value=1000, max_value=200000, value=5500, step=250)
                f_class = st.selectbox("Travel Class", ["Economy", "Premium Economy", "Business", "First Class"])
                f_dur = st.number_input("Duration (Minutes)", min_value=30, max_value=1200, value=150)
                f_stops = st.selectbox("Stops", [0, 1, 2])

                if st.form_submit_button("Publish Flight Route"):
                    if not f_num.strip() or not f_src.strip() or not f_dst.strip():
                        st.error("Flight number, source, and destination required.")
                    else:
                        now = datetime.datetime.now()
                        dep = now + datetime.timedelta(days=7, hours=10)
                        arr = dep + datetime.timedelta(minutes=f_dur)
                        q = """
                            INSERT INTO flights (flight_number, airline, source_city, destination_city, departure_time, arrival_time, duration_minutes, stops, travel_class, price, seats_available, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        try:
                            execute_commit(q, (f_num.strip(), f_air, f_src.strip(), f_dst.strip(), dep, arr, f_dur, f_stops, f_class, f_price, 60, now))
                            st.success(f"Flight '{f_num}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding flight: {str(e)}")

        else:
            recent_flights = fetch_all("SELECT * FROM flights ORDER BY flight_id DESC LIMIT 20")
            for fl in recent_flights:
                c_info, c_act = st.columns([5, 1])
                with c_info:
                    st.markdown(f"**{fl['flight_number']}** &bull; {fl['airline']} &bull; `{fl['source_city']} ➔ {fl['destination_city']}` &bull; `{fl['travel_class']}` &bull; `{format_currency(fl['price'])}`")
                with c_act:
                    if st.button("🗑️ Delete", key=f"del_fl_{fl['flight_id']}"):
                        execute_commit("DELETE FROM flights WHERE flight_id = %s", (fl["flight_id"],))
                        st.warning("Flight removed.")
                        st.rerun()

    # ========================================================
    # 5. HOTELS CRUD
    # ========================================================
    with tab_hotels:
        st.subheader("Manage Hotel Catalog")
        all_dests = fetch_all("SELECT destination_id, name FROM destinations ORDER BY name ASC")
        dest_map = {d["name"]: d["destination_id"] for d in all_dests}

        h_action = st.radio("Hotel Action", ["View All / Filter", "Add New Hotel"], horizontal=True)

        if h_action == "Add New Hotel":
            with st.form("add_hotel_form"):
                h_name = st.text_input("Hotel Name (e.g. Taj Exotica Resort)")
                h_dest = st.selectbox("Associated Destination", list(dest_map.keys()) if dest_map else ["Goa"])
                h_addr = st.text_input("Full Address")
                h_star = st.slider("Star Rating", 1, 5, 4)
                h_ptype = st.selectbox("Property Type", ["Luxury Resort", "Boutique Hotel", "Heritage Palace", "Business Hotel", "Eco Lodge"])
                h_amen = st.text_area("Amenities (comma-separated)", value="Free Wi-Fi, Swimming Pool, Spa, Ocean View, Breakfast")
                h_price = st.number_input("Base Price Per Night (₹)", min_value=1000, max_value=100000, value=7500)
                h_img = st.text_input("Image URL")

                if st.form_submit_button("Add Hotel"):
                    if not h_name.strip() or not h_addr.strip():
                        st.error("Hotel name and address required.")
                    else:
                        d_id = dest_map[h_dest]
                        img_to_use = h_img.strip() if h_img.strip() else get_image_url("", "Hotel")
                        q = """
                            INSERT INTO hotels (name, destination_id, city, address, star_rating, property_type, amenities, price_per_night, image_url, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        try:
                            execute_commit(q, (h_name.strip(), d_id, h_dest, h_addr.strip(), h_star, h_ptype, h_amen.strip(), h_price, img_to_use, datetime.datetime.now()))
                            st.success(f"Hotel '{h_name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding hotel: {str(e)}")

        else:
            recent_hotels = fetch_all("""
                SELECT h.*, d.name as dest_name
                FROM hotels h
                JOIN destinations d ON h.destination_id = d.destination_id
                ORDER BY h.hotel_id DESC LIMIT 15
            """)
            for ht in recent_hotels:
                c_info, c_act = st.columns([5, 1])
                with c_info:
                    st.markdown(f"**{ht['name']}** ({ht['dest_name']}) &bull; `{ht['property_type']}` &bull; {ht['star_rating']}★ &bull; Price: `{format_currency(ht['price_per_night'])}`/night")
                with c_act:
                    if st.button("🗑️ Delete", key=f"del_ht_{ht['hotel_id']}"):
                        execute_commit("DELETE FROM hotels WHERE hotel_id = %s", (ht["hotel_id"],))
                        st.warning("Hotel removed.")
                        st.rerun()

    # ========================================================
    # 6. BOOKINGS MANAGER
    # ========================================================
    with tab_bookings:
        st.subheader("Customer Bookings Moderation")
        b_filter = st.selectbox("Filter Status", ["All", "Confirmed", "Pending", "Completed", "Cancelled"])

        q = """
            SELECT b.*, u.full_name, u.email
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
        """
        p = []
        if b_filter != "All":
            q += " WHERE b.status = %s"
            p.append(b_filter)
        q += " ORDER BY b.booking_date DESC LIMIT 40"

        admin_bookings = fetch_all(q, tuple(p) if p else None)
        st.markdown(f"Found **{len(admin_bookings)}** booking entries.")

        for ab in admin_bookings:
            badge_html = get_status_badge(ab["status"])
            st.markdown(f"""
            <div style="background: #1E293B; border-radius: 12px; padding: 14px 18px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.06);">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <b>{ab['booking_reference']}</b> &bull; Customer: <span style="color: #38BDF8;">{ab['full_name']}</span> ({ab['email']})
                        <div style="font-size: 0.9rem; color: #E2E8F0; margin-top: 2px;">{ab['item_title']} ({ab['booking_type']}) &bull; Paid: <b style="color: #34D399;">{format_currency(ab['total_price'])}</b></div>
                    </div>
                    <div>{badge_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_s1, _ = st.columns([2, 4])
            with col_s1:
                new_st = st.selectbox(
                    f"Change Status for {ab['booking_reference']}",
                    ["Confirmed", "Completed", "Cancelled", "Pending"],
                    index=["Confirmed", "Completed", "Cancelled", "Pending"].index(ab["status"]),
                    key=f"status_sel_{ab['booking_id']}"
                )
                if new_st != ab["status"]:
                    execute_commit("UPDATE bookings SET status = %s WHERE booking_id = %s", (new_st, ab["booking_id"]))
                    st.success(f"Status updated to {new_st}")
                    st.rerun()

    # ========================================================
    # 7. REVIEW MODERATION
    # ========================================================
    with tab_reviews:
        st.subheader("Traveler Reviews Moderation")
        all_revs = fetch_all("""
            SELECT r.*, u.full_name, u.email
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            ORDER BY r.created_at DESC LIMIT 25
        """)
        for rev in all_revs:
            col_r_info, col_r_del = st.columns([5, 1])
            with col_r_info:
                st.markdown(f"**{rev['title']}** ({rev['rating']}★) by `{rev['full_name']}` ({rev['email']})\n*\"{rev['comment']}\"*")
            with col_r_del:
                if st.button("Delete Review", key=f"adm_del_rev_{rev['review_id']}"):
                    execute_commit("DELETE FROM reviews WHERE review_id = %s", (rev["review_id"],))
                    st.warning("Review deleted.")
                    st.rerun()

    # ========================================================
    # 8. DATABASE STATS & SYSTEM DIAGNOSTICS
    # ========================================================
    with tab_system:
        st.subheader("📊 Relational Database Record Audit")
        st.caption("Live row counts verified directly across MySQL tables:")

        counts = get_table_counts()
        df_counts = pd.DataFrame(list(counts.items()), columns=["Database Table", "Total Records"])
        st.dataframe(df_counts, use_container_width=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0;'/>", unsafe_allow_html=True)
        st.markdown("### 🔄 Dataset Synchronization")
        st.caption("Synchronize relational datasets or verify integrity across all entities.")

        if st.button("⚡ Run Dataset Sync / Verify", use_container_width=True):
            from seed_data import seed_all_data
            seed_all_data(force_reset=False)
            st.success("Seed dataset synchronized successfully!")
            st.rerun()
