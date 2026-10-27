"""
YATRIVO — Reviews & Community Ratings Module
Traveler testimonials, verified star ratings, and duplicate-prevention review submission.
"""

import streamlit as st
import datetime
from database import fetch_all, fetch_one, execute_commit
from utils.formatting import render_stars, format_datetime
from auth import get_current_user, is_authenticated


def render_reviews():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            ⭐ Traveler Reviews & Ratings
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Read authentic feedback from fellow travelers and submit your own ratings for destinations and hotels.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_browse, tab_submit = st.tabs(["💬 Browse Traveler Reviews", "✍️ Write a Review"])

    # ========================================================
    # TAB 1: BROWSE REVIEWS
    # ========================================================
    with tab_browse:
        r_col1, r_col2 = st.columns([2, 2])
        with r_col1:
            target_filter = st.selectbox("Filter Target Type", ["All Types", "Destinations", "Hotels"])
        with r_col2:
            rating_filter = st.selectbox("Filter by Rating", ["All Ratings", "5 Stars Only", "4+ Stars", "3 Stars & Below"])

        # Construct Query
        rev_query = """
            SELECT r.*, u.full_name
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE 1=1
        """
        rev_params = []
        if target_filter == "Destinations":
            rev_query += " AND r.target_type = 'destination'"
        elif target_filter == "Hotels":
            rev_query += " AND r.target_type = 'hotel'"

        if rating_filter == "5 Stars Only":
            rev_query += " AND r.rating = 5"
        elif rating_filter == "4+ Stars":
            rev_query += " AND r.rating >= 4"
        elif rating_filter == "3 Stars & Below":
            rev_query += " AND r.rating <= 3"

        rev_query += " ORDER BY r.created_at DESC LIMIT 50"
        all_reviews = fetch_all(rev_query, tuple(rev_params) if rev_params else None)

        # Overview Stats
        avg_row = fetch_one("SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews")
        avg_val = float(avg_row["avg_r"]) if avg_row and avg_row["avg_r"] else 4.5
        total_cnt = avg_row["cnt"] if avg_row else 0

        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            st.metric("Total Reviews", total_cnt)
        with s_col2:
            st.metric("Average Rating", f"{avg_val:.2f} / 5.0", delta=render_stars(avg_val))
        with s_col3:
            st.metric("Verified Travelers", "100%", delta="Authenticated Community")

        st.markdown(f"<div style='color: #94A3B8; font-size: 0.95rem; margin: 16px 0 14px 0;'>Showing <b>{len(all_reviews)}</b> review(s)</div>", unsafe_allow_html=True)

        for rev in all_reviews:
            # Fetch target item name
            target_name = "N/A"
            if rev["target_type"] == "destination":
                d_row = fetch_one("SELECT name, state_country FROM destinations WHERE destination_id = %s", (rev["target_id"],))
                target_name = f"Destination: {d_row['name']} ({d_row['state_country']})" if d_row else "Destination"
            else:
                h_row = fetch_one("SELECT name, city FROM hotels WHERE hotel_id = %s", (rev["target_id"],))
                target_name = f"Hotel: {h_row['name']} ({h_row['city']})" if h_row else "Hotel"

            st.markdown(f"""
            <div style="
                background: #1E293B;
                border-radius: 14px;
                padding: 18px 22px;
                margin-bottom: 14px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            ">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                    <div>
                        <span style="font-size: 0.8rem; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.12); padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{rev['target_type']}</span>
                        <span style="font-size: 0.95rem; font-weight: 700; color: #CBD5E1; margin-left: 8px;">{target_name}</span>
                    </div>
                    <div style="color: #FBBF24; font-size: 1rem; font-weight: 700;">{render_stars(rev['rating'])} ({rev['rating']}/5)</div>
                </div>
                <h4 style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0;">{rev['title']}</h4>
                <p style="font-size: 0.9rem; color: #94A3B8; line-height: 1.5; margin: 0 0 10px 0;">\"{rev['comment']}\"</p>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748B;">
                    <span>By: <b style="color: #E2E8F0;">{rev['full_name']}</b></span>
                    <span>{format_datetime(rev['created_at'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ========================================================
    # TAB 2: WRITE A REVIEW
    # ========================================================
    with tab_submit:
        user = get_current_user()
        if not is_authenticated() or not user:
            st.warning("🔒 Please log in with your customer account to submit a review.")
            return

        uid = user["user_id"]

        st.markdown("### ✍️ Share Your Travel Experience")
        target_choice = st.radio("What would you like to review?", ["Destination", "Hotel"], horizontal=True)

        if target_choice == "Destination":
            dest_list = fetch_all("SELECT destination_id, name, city, state_country FROM destinations ORDER BY name")
            item_map = {f"{d['name']} ({d['city']}, {d['state_country']})": d["destination_id"] for d in dest_list}
            t_type_val = "destination"
        else:
            hotel_list = fetch_all("SELECT hotel_id, name, city FROM hotels ORDER BY name LIMIT 100")
            item_map = {f"{h['name']} ({h['city']})": h["hotel_id"] for h in hotel_list}
            t_type_val = "hotel"

        with st.form("submit_review_form"):
            selected_item_label = st.selectbox(f"Select {target_choice}", list(item_map.keys()))
            target_id_val = item_map[selected_item_label]

            score = st.slider("Rating (1 = Poor, 5 = Outstanding)", min_value=1, max_value=5, value=5)
            rev_title = st.text_input("Review Title / Headline", placeholder="e.g. Unbelievable mountain scenery and great service!")
            rev_comment = st.text_area("Your Detailed Feedback", placeholder="Share tips, highlights, and recommendations for other travelers...")

            submit_rev = st.form_submit_button("Post Review", use_container_width=True)

            if submit_rev:
                if not rev_title.strip() or not rev_comment.strip():
                    st.error("Please provide both a title and review text.")
                else:
                    # Check uniqueness constraint
                    dup = fetch_one(
                        "SELECT review_id FROM reviews WHERE user_id = %s AND target_type = %s AND target_id = %s",
                        (uid, t_type_val, target_id_val)
                    )
                    if dup:
                        st.error(f"You have already submitted a review for this {target_choice}. You cannot post duplicate reviews.")
                    else:
                        now = datetime.datetime.now()
                        insert_query = """
                            INSERT INTO reviews (user_id, target_type, target_id, rating, title, comment, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        try:
                            execute_commit(insert_query, (uid, t_type_val, target_id_val, score, rev_title.strip(), rev_comment.strip(), now))
                            st.success("🎉 Thank you! Your review has been published successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to submit review: {str(e)}")
