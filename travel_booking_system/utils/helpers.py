"""
General Helper Functions for TRAVELNEST
"""

import random
import string
import datetime
import pandas as pd
from typing import Optional, Dict


FALLBACK_IMAGES = {
    "Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
    "Mountain": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80",
    "Heritage": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80",
    "Urban": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=800&q=80",
    "Wildlife": "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=800&q=80",
    "Adventure": "https://images.unsplash.com/photo-1527631746610-bca00a040d60?auto=format&fit=crop&w=800&q=80",
    "Island": "https://images.unsplash.com/photo-1512100356356-de1b84283e18?auto=format&fit=crop&w=800&q=80",
    "Spiritual": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80",
    "Hotel": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
    "Flight": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=800&q=80",
    "Package": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80",
    "Default": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80"
}


def get_image_url(url: Optional[str], category: str = "Default") -> str:
    """Returns valid image URL or a category fallback if URL is empty or invalid."""
    if url and url.startswith("http"):
        return url
    return FALLBACK_IMAGES.get(category, FALLBACK_IMAGES["Default"])


def generate_booking_reference(item_type: str = "GEN") -> str:
    """Generates unique, realistic booking reference (e.g. TN-FL-83921, TN-HT-19284)."""
    type_code = {
        "Flight": "FL",
        "Hotel": "HT",
        "Package": "PK",
        "Activity": "AC"
    }.get(item_type, "BK")
    rand_digits = "".join(random.choices(string.digits, k=5))
    rand_chars = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"TN-{type_code}-{rand_digits}{rand_chars}"


def calculate_stay_nights(check_in: datetime.date, check_out: datetime.date) -> int:
    """Calculates number of nights between two dates (minimum 1 night)."""
    if not check_in or not check_out:
        return 1
    delta = (check_out - check_in).days
    return max(1, delta)


def truncate_text(text: str, max_len: int = 120) -> str:
    """Truncates string to max_len with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Converts a pandas DataFrame to UTF-8 CSV bytes for Streamlit download button."""
    return df.to_csv(index=False).encode("utf-8")
