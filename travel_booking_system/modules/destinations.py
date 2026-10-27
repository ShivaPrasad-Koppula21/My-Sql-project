"""
YATRIVO — Explore Destinations Module
Comprehensive destination catalog with multi-facet filters, sorting, high-res cards, and detailed modal views.
"""

import streamlit as st
import math
from database import fetch_all, fetch_one
from utils.formatting import format_currency, render_stars
from utils.helpers import get_image_url, truncate_text


def render_destinations():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            🗺️ Explore Destinations
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Discover 60+ breathtaking destinations across India and iconic international capitals.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Search & Filter Controls ---
    with st.container():
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

        initial_search = st.session_state.pop("search_destination_filter", "")

        with c1:
            search_query = st.text_input("🔍 Search Destination or City", value=initial_search, placeholder="e.g. Goa, Paris, Manali, Tokyo...")

        with c2:
            country_options = ["All Countries", "India", "International"]
            sel_country = st.selectbox("🌍 Region / Country", country_options)

        with c3:
            category_options = ["All Categories", "Beach", "Mountain", "Heritage", "Urban", "Wildlife", "Adventure", "Island", "Spiritual"]
            sel_category = st.selectbox("🏷️ Theme / Category", category_options)

        with c4:
            sort_by = st.selectbox("↕️ Sort By", ["Highest Rated", "Budget: Low to High", "Budget: High to Low", "Name (A-Z)"])

    # Price range slider
    max_budget_limit = 200000
    budget_range = st.slider("💰 Estimated Budget Range (₹)", min_value=5000, max_value=max_budget_limit, value=(5000, max_budget_limit), step=5000)

    # --- SQL Query Construction ---
    query = "SELECT * FROM destinations WHERE estimated_budget BETWEEN %s AND %s"
    params = [budget_range[0], budget_range[1]]

    if search_query.strip():
        query += " AND (LOWER(name) LIKE %s OR LOWER(city) LIKE %s OR LOWER(state_country) LIKE %s OR LOWER(description) LIKE %s)"
        term = f"%{search_query.strip().lower()}%"
        params.extend([term, term, term, term])

    if sel_country == "India":
        query += " AND LOWER(state_country) = 'india'"
    elif sel_country == "International":
        query += " AND LOWER(state_country) != 'india'"

    if sel_category != "All Categories":
        query += " AND category = %s"
        params.append(sel_category)

    # Order by
    if sort_by == "Highest Rated":
        query += " ORDER BY rating DESC"
    elif sort_by == "Budget: Low to High":
        query += " ORDER BY estimated_budget ASC"
    elif sort_by == "Budget: High to Low":
        query += " ORDER BY estimated_budget DESC"
    elif sort_by == "Name (A-Z)":
        query += " ORDER BY name ASC"

    destinations = fetch_all(query, tuple(params))

    # --- Results Summary & Pagination ---
    total_found = len(destinations)
    st.markdown(f"<div style='color: #94A3B8; font-size: 0.95rem; margin: 16px 0 20px 0;'>Showing <b>{total_found}</b> matching destination(s)</div>", unsafe_allow_html=True)

    if not destinations:
        st.info("No destinations found matching your criteria. Try adjusting the search keywords or filters.")
        return

    # Pagination setup (9 per page)
    items_per_page = 9
    total_pages = max(1, math.ceil(total_found / items_per_page))

    if "dest_page" not in st.session_state:
        st.session_state["dest_page"] = 1

    current_page = st.session_state["dest_page"]
    if current_page > total_pages:
        current_page = 1
        st.session_state["dest_page"] = 1

    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = destinations[start_idx:end_idx]

    # --- Grid Display ---
    cols_per_row = 3
    for i in range(0, len(page_items), cols_per_row):
        row_items = page_items[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for c_idx, d in enumerate(row_items):
            with cols[c_idx]:
                img_url = get_image_url(d.get("image_url"), d.get("category", "Heritage"))
                st.markdown(f"""
                <div style="
                    background: #1E293B;
                    border-radius: 16px;
                    overflow: hidden;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    margin-bottom: 12px;
                    display: flex;
                    flex-direction: column;
                    height: 440px;
                ">
                    <img src="{img_url}" style="width: 100%; height: 190px; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80';"/>
                    <div style="padding: 16px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #38BDF8; background: rgba(56, 189, 248, 0.12); padding: 3px 8px; border-radius: 4px;">{d['category']}</span>
                                <span style="font-size: 0.85rem; color: #FBBF24; font-weight: 700;">★ {d['rating']:.1f}</span>
                            </div>
                            <h3 style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 0 0 2px 0;">{d['name']}</h3>
                            <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 8px;">📍 {d['city']}, {d['state_country']}</div>
                            <p style="font-size: 0.84rem; color: #CBD5E1; line-height: 1.4; margin: 0 0 8px 0; height: 50px; overflow: hidden;">{truncate_text(d['description'], 90)}</p>
                        </div>
                        <div>
                            <div style="font-size: 0.78rem; color: #64748B; margin-bottom: 4px;">🗓️ Best Time: <b style="color: #E2E8F0;">{d.get('best_time_to_visit', 'All Year')}</b></div>
                            <div style="display: flex; justify-content: space-between; align-items: baseline; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                                <span style="font-size: 0.78rem; color: #94A3B8;">Est. Budget</span>
                                <span style="font-size: 1.15rem; font-weight: 800; color: #34D399;">{format_currency(d['estimated_budget'])}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("ℹ️ Details", key=f"det_{d['destination_id']}", use_container_width=True):
                        st.session_state["active_dest_modal"] = d["destination_id"]
                with btn_col2:
                    if st.button("🏨 Find Hotels", key=f"htl_{d['destination_id']}", use_container_width=True):
                        st.session_state["nav_selection"] = "Hotel Explorer"
                        st.session_state["hotel_dest_filter"] = d["destination_id"]
                        st.rerun()

    # --- Pagination Buttons ---
    if total_pages > 1:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if current_page > 1:
                if st.button("⬅️ Previous Page", use_container_width=True):
                    st.session_state["dest_page"] = current_page - 1
                    st.rerun()
        with p_col2:
            st.markdown(f"<div style='text-align: center; color: #94A3B8; padding-top: 8px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
        with p_col3:
            if current_page < total_pages:
                if st.button("Next Page ➡️", use_container_width=True):
                    st.session_state["dest_page"] = current_page + 1
                    st.rerun()

    # --- Details Modal / Expander if clicked ---
    active_modal_id = st.session_state.get("active_dest_modal")
    if active_modal_id:
        target_dest = fetch_one("SELECT * FROM destinations WHERE destination_id = %s", (active_modal_id,))
        if target_dest:
            st.markdown("<hr style='border-color: rgba(56, 189, 248, 0.3); margin: 30px 0;'/>", unsafe_allow_html=True)
            st.markdown(f"### 📍 Detailed Guide: {target_dest['name']} ({target_dest['city']}, {target_dest['state_country']})")

            m_col1, m_col2 = st.columns([1, 1])
            with m_col1:
                img_url = get_image_url(target_dest.get("image_url"), target_dest.get("category"))
                st.image(img_url, use_column_width=True, caption=f"{target_dest['name']} — {target_dest['category']}")
            with m_col2:
                st.markdown(f"**Category:** `{target_dest['category']}`")
                st.markdown(f"**Community Rating:** {render_stars(target_dest['rating'])} ({target_dest['rating']:.1f}/5.0)")
                st.markdown(f"**Best Months to Visit:** `{target_dest.get('best_time_to_visit', 'Oct - Mar')}`")
                st.markdown(f"**Typical Traveler Budget:** `{format_currency(target_dest['estimated_budget'])}`")
                st.markdown(f"**Overview:**\n\n{target_dest['description']}")

                # Reviews for this destination
                reviews = fetch_all("""
                    SELECT r.*, u.full_name
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.target_type = 'destination' AND r.target_id = %s
                    ORDER BY r.created_at DESC LIMIT 3
                """, (active_modal_id,))

                if reviews:
                    st.markdown("#### 💬 Recent Traveler Reviews")
                    for rev in reviews:
                        st.markdown(f"- **{rev['full_name']}** ({render_stars(rev['rating'])}): *\"{rev['comment']}\"*")
                else:
                    st.caption("No traveler reviews yet. Be the first to review!")

            if st.button("Close Details", key="close_dest_modal"):
                del st.session_state["active_dest_modal"]
                st.rerun()
