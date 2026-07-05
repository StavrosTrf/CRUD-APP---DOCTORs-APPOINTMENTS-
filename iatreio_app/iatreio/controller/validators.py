"""Επικυρωτές εισόδου του επιχειρησιακού επιπέδου.

Καθαρές συναρτήσεις που σηκώνουν ValidationError όταν τα δεδομένα δεν είναι
έγκυρα. Δεν εξαρτώνται από βάση ή UI, ώστε να είναι εύκολα ελέγξιμες.
"""
from __future__ import annotations

import re
from datetime import datetime

from ..util.security import is_valid_amka
from .exceptions import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DT_FORMAT = "%Y-%m-%d %H:%M"

# Ωράριο λειτουργίας ιατρείου (UC005 — Διαθεσιμότητα Ιατρού).
CLINIC_OPEN_HOUR = 9
CLINIC_CLOSE_HOUR = 21


def require_nonempty(value: str, field_name: str) -> str:
    if value is None or str(value).strip() == "":
        raise ValidationError(f"Το πεδίο «{field_name}» είναι υποχρεωτικό.")
    return str(value).strip()


def validate_amka(amka: str) -> str:
    amka = (amka or "").strip()
    if not is_valid_amka(amka):
        raise ValidationError(
            "Μη έγκυρος ΑΜΚΑ. Απαιτούνται 11 ψηφία με σωστό ψηφίο ελέγχου."
        )
    return amka


def validate_email(email: str, *, allow_empty: bool = True) -> str:
    email = (email or "").strip()
    if email == "":
        if allow_empty:
            return ""
        raise ValidationError("Το email είναι υποχρεωτικό.")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Μη έγκυρη διεύθυνση email.")
    return email


def parse_datetime(value: str) -> datetime:
    """Μετατρέπει string 'YYYY-MM-DD HH:MM' σε datetime, αλλιώς ValidationError."""
    value = (value or "").strip()
    try:
        return datetime.strptime(value, _DT_FORMAT)
    except ValueError:
        raise ValidationError(
            "Μη έγκυρη ημερομηνία/ώρα. Χρησιμοποιήστε μορφή ΕΕΕΕ-ΜΜ-ΗΗ ΩΩ:ΛΛ."
        )


def validate_within_working_hours(dt: datetime) -> None:
    if not (CLINIC_OPEN_HOUR <= dt.hour < CLINIC_CLOSE_HOUR):
        raise ValidationError(
            f"Η ώρα πρέπει να είναι εντός ωραρίου "
            f"({CLINIC_OPEN_HOUR:02d}:00–{CLINIC_CLOSE_HOUR:02d}:00)."
        )
