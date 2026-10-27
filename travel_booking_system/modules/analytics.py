"""
YATRIVO — Data Analytics & Business Intelligence Module
Interactive Plotly visualizations, revenue distributions, booking trends, and CSV data export.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import fetch_dataframe, fetch_one
from utils.formatting import format_currency
from utils.helpers import dataframe_to_csv_bytes


def render_analytics():
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #F8FAFC; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">
            📈 Data Analytics & Executive Reports
        </h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Real-time business intelligence calculated directly from relational database transactions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch live booking dataset
    query = """
        SELECT
            booking_id,
            booking_reference,
            booking_type,
            item_title,
            booking_date,
            travel_start_date,
            num_guests,
            unit_price,
            total_price,
            status
        FROM bookings
    """
    df_bookings = fetch_dataframe(query)

    if df_bookings.empty:
        st.warning("No booking records available for analytics. Please ensure seed data is loaded.")
        return

    # Convert dates
    df_bookings["booking_date"] = pd.to_datetime(df_bookings["booking_date"])
    df_bookings["booking_month"] = df_bookings["booking_date"].dt.strftime("%Y-%m")
    df_bookings["total_price"] = pd.to_numeric(df_bookings["total_price"], errors="coerce")

    # --- Top KPI Summary Metrics ---
    total_revenue = df_bookings[df_bookings["status"] != "Cancelled"]["total_price"].sum()
    total_count = len(df_bookings)
    completed_count = len(df_bookings[df_bookings["status"] == "Completed"])
    cancelled_count = len(df_bookings[df_bookings["status"] == "Cancelled"])
    cancellation_rate = (cancelled_count / total_count * 100) if total_count > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Platform Revenue", format_currency(total_revenue), delta="Net Realized")
    with k2:
        st.metric("Gross Bookings", total_count, delta="Across All Verticals")
    with k3:
        st.metric("Completed Trips", completed_count, delta="Successful Vouchers")
    with k4:
        st.metric("Cancellation Rate", f"{cancellation_rate:.1f}%", delta=f"{cancelled_count} Cancelled")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- Chart Section 1: Revenue by Category & Booking Status ---
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.markdown("### 🍩 Revenue Breakdown by Category")
        rev_by_type = (
            df_bookings[df_bookings["status"] != "Cancelled"]
            .groupby("booking_type")["total_price"]
            .sum()
            .reset_index()
        )
        fig_rev = px.pie(
            rev_by_type,
            names="booking_type",
            values="total_price",
            hole=0.45,
            color="booking_type",
            color_discrete_map={
                "Flight": "#38BDF8",
                "Hotel": "#10B981",
                "Package": "#F59E0B",
                "Activity": "#A855F7"
            }
        )
        fig_rev.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2)
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    with c_col2:
        st.markdown("### 📊 Booking Status Distribution")
        status_counts = df_bookings["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]

        fig_status = px.bar(
            status_counts,
            x="status",
            y="count",
            color="status",
            color_discrete_map={
                "Confirmed": "#10B981",
                "Completed": "#3B82F6",
                "Pending": "#F59E0B",
                "Cancelled": "#EF4444"
            },
            text="count"
        )
        fig_status.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1"),
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title="Bookings Count"),
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- Chart Section 2: Booking Trends over Time ---
    st.markdown("### 📈 Monthly Booking Volume & Sales Trend")
    trend_df = (
        df_bookings.groupby(["booking_month", "booking_type"])
        .agg(total_volume=("booking_id", "count"), total_sales=("total_price", "sum"))
        .reset_index()
        .sort_values("booking_month")
    )

    fig_trend = px.line(
        trend_df,
        x="booking_month",
        y="total_sales",
        color="booking_type",
        markers=True,
        color_discrete_map={
            "Flight": "#38BDF8",
            "Hotel": "#10B981",
            "Package": "#F59E0B",
            "Activity": "#A855F7"
        }
    )
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title="Month"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title="Sales (₹)"),
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- Chart Section 3: Popular Destinations & Hotel Price Distribution ---
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        st.markdown("### 🏆 Top 10 Destinations by Traveler Ratings")
        dest_df = fetch_dataframe("SELECT name, state_country, rating, estimated_budget FROM destinations ORDER BY rating DESC LIMIT 10")
        if not dest_df.empty:
            dest_df["dest_label"] = dest_df["name"] + " (" + dest_df["state_country"] + ")"
            fig_dest = px.bar(
                dest_df,
                x="rating",
                y="dest_label",
                orientation="h",
                color="rating",
                color_continuous_scale="teal",
                text="rating"
            )
            fig_dest.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#CBD5E1"),
                xaxis=dict(range=[4.0, 5.0], title="Rating (Out of 5)"),
                yaxis=dict(autorange="reversed", title=""),
                margin=dict(t=20, b=20, l=20, r=20),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_dest, use_container_width=True)

    with d_col2:
        st.markdown("### 🏷️ Flight Fare Distribution by Travel Class")
        flights_df = fetch_dataframe("SELECT airline, travel_class, price FROM flights LIMIT 300")
        if not flights_df.empty:
            fig_box = px.box(
                flights_df,
                x="travel_class",
                y="price",
                color="travel_class",
                color_discrete_map={
                    "Economy": "#38BDF8",
                    "Premium Economy": "#818CF8",
                    "Business": "#F59E0B",
                    "First": "#EC4899"
                }
            )
            fig_box.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#CBD5E1"),
                xaxis=dict(title="Cabin Class"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title="Fare (₹)"),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False
            )
            st.plotly_chart(fig_box, use_container_width=True)

    # --- Interactive Tabular Report & CSV Export ---
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 30px 0;'/>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Filtered Business Reports (CSV)")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sel_rep_type = st.selectbox("Report Filter: Booking Type", ["All Types", "Flight", "Hotel", "Package", "Activity"])
    with f_col2:
        sel_rep_status = st.selectbox("Report Filter: Status", ["All Statuses", "Confirmed", "Completed", "Cancelled", "Pending"])
    with f_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        # Apply filters
        df_export = df_bookings.copy()
        if sel_rep_type != "All Types":
            df_export = df_export[df_export["booking_type"] == sel_rep_type]
        if sel_rep_status != "All Statuses":
            df_export = df_export[df_export["status"] == sel_rep_status]

        csv_bytes = dataframe_to_csv_bytes(df_export)
        st.download_button(
            label="⬇️ Download CSV Report",
            data=csv_bytes,
            file_name=f"yatrivo_bookings_report_{sel_rep_type.lower()}_{sel_rep_status.lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown(f"**Report Preview ({len(df_export)} records):**")
    st.dataframe(
        df_export[["booking_reference", "booking_type", "item_title", "travel_start_date", "num_guests", "total_price", "status"]].head(15),
        use_container_width=True
    )
