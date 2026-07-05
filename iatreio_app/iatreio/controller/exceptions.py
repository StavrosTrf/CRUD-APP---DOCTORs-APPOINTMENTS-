"""Εξαιρέσεις του επιπέδου επιχειρησιακής λογικής.

Διαχωρίζονται από τις τεχνικές εξαιρέσεις της sqlite3 ώστε το View να μπορεί
να εμφανίζει φιλικά μηνύματα στον χρήστη.
"""


class AppError(Exception):
    """Βασική εξαίρεση εφαρμογής."""


class ValidationError(AppError):
    """Μη έγκυρα δεδομένα εισόδου (π.χ. λανθασμένος ΑΜΚΑ)."""


class AuthenticationError(AppError):
    """Αποτυχία αυθεντικοποίησης (UC001)."""


class BusinessRuleError(AppError):
    """Παραβίαση επιχειρησιακού κανόνα (π.χ. double-booking)."""


class NotFoundError(AppError):
    """Η ζητούμενη οντότητα δεν βρέθηκε."""
