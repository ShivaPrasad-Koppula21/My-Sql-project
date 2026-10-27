"""
Formatting and presentation helpers for TRAVELNEST
"""

import datetime
from typing import Union


def format_currency(amount: Union[int, float], currency_symbol: str = "₹") -> str:
    """Formats numeric value as currency (e.g. ₹12,500.00)."""
    try:
        val = float(amount)
        return f"{currency_symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"


def format_currency_short(amount: Union[int, float], currency_symbol: str = "₹") -> str:
    """Formats large amounts compactly (e.g. ₹1.2L or ₹45K)."""
    try:
        val = float(amount)
        if val >= 10000000:
            return f"{currency_symbol}{val/10000000:.1f} Cr"
        elif val >= 100000:
            return f"{currency_symbol}{val/100000:.1f} L"
        elif val >= 1000:
            return f"{currency_symbol}{val/1000:.1f} K"
        return f"{currency_symbol}{val:.0f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0"


def format_date(dt: Union[datetime.date, datetime.datetime, str]) -> str:
    """Formats date object or ISO string to readable format (e.g., 14 Oct 2026)."""
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt[:10]
    return dt.strftime("%d %b %Y")


def format_datetime(dt: Union[datetime.datetime, str]) -> str:
    """Formats datetime object or ISO string to readable string."""
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt
    return dt.strftime("%d %b %Y, %I:%M %p")


def format_duration(minutes: int) -> str:
    """Converts minutes to hours and minutes string (e.g. 2h 45m)."""
    try:
        m = int(minutes)
        hrs = m // 60
        mins = m % 60
        if hrs > 0 and mins > 0:
            return f"{hrs}h {mins}m"
        elif hrs > 0:
            return f"{hrs}h"
        return f"{mins}m"
    except Exception:
        return f"{minutes}m"


def render_stars(rating: float) -> str:
    """Renders rating as star symbols (e.g. ★★★★☆)."""
    try:
        r = round(float(rating))
        r = max(1, min(5, r))
        return "★" * r + "☆" * (5 - r)
    except Exception:
        return "★★★★☆"


def get_status_badge(status: str) -> str:
    """Returns styled HTML badge for booking or trip status."""
    st_clean = (status or "").capitalize()
    color_map = {
        "Confirmed": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#10B981", "border": "#10B981"},
        "Completed": {"bg": "rgba(59, 130, 246, 0.15)", "text": "#60A5FA", "border": "#3B82F6"},
        "Pending": {"bg": "rgba(245, 158, 11, 0.15)", "text": "#FBBF24", "border": "#F59E0B"},
        "Cancelled": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#F87171", "border": "#EF4444"},
        "Upcoming": {"bg": "rgba(14, 165, 233, 0.15)", "text": "#38BDF8", "border": "#0EA5E9"},
        "Planning": {"bg": "rgba(168, 85, 247, 0.15)", "text": "#C084FC", "border": "#A855F7"}
    }
    c = color_map.get(st_clean, {"bg": "rgba(100, 116, 139, 0.15)", "text": "#94A3B8", "border": "#64748B"})
    return f"""<span style="
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        background-color: {c['bg']};
        color: {c['text']};
        border: 1px solid {c['border']};
    ">{st_clean}</span>"""
