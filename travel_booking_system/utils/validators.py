"""
Validation utilities for TRAVELNEST
"""

import re
import datetime
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    if not email or not isinstance(email, str):
        return False, "Email cannot be empty."
    email = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Invalid email format (e.g., traveler@example.com)."
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    if not phone:
        return True, ""  # Phone is optional
    phone = phone.strip()
    pattern = r"^\+?[0-9\s-]{8,15}$"
    if not re.match(pattern, phone):
        return False, "Invalid phone number. Expected 8-15 digits with optional '+' prefix."
    return True, ""


def validate_date_range(start_date: datetime.date, end_date: datetime.date) -> Tuple[bool, str]:
    if not start_date or not end_date:
        return False, "Both start date and end date are required."
    if end_date < start_date:
        return False, "End date cannot be earlier than start date."
    return True, ""


def validate_positive_number(val: float, name: str = "Amount") -> Tuple[bool, str]:
    try:
        val_f = float(val)
        if val_f <= 0:
            return False, f"{name} must be greater than zero."
        return True, ""
    except (ValueError, TypeError):
        return False, f"{name} must be a valid number."
