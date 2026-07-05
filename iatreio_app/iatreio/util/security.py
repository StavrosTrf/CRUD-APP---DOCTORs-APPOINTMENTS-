"""Βοηθητικές συναρτήσεις ασφαλείας.

Περιλαμβάνει ασφαλή κατακερματισμό κωδικών (PBKDF2-HMAC-SHA256, §4.2 του SRS)
και επικύρωση ΑΜΚΑ με αλγόριθμο Luhn.

Το module ανήκει σε επίπεδο "cross-cutting utility" και δεν εξαρτάται από
την Tkinter ούτε από τη βάση δεδομένων.
"""
from __future__ import annotations

import hashlib
import hmac
import os

# Επαναλήψεις PBKDF2. Σε production θα ήταν υψηλότερο· κρατιέται μέτριο για ταχύτητα tests.
_ITERATIONS = 100_000


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Κατακερματίζει έναν κωδικό με PBKDF2-HMAC-SHA256.

    Επιστρέφει tuple (hash_hex, salt_hex). Αν δεν δοθεί salt, δημιουργείται νέο.
    """
    if password is None:
        raise ValueError("Ο κωδικός δεν μπορεί να είναι None")
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return dk.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Επαληθεύει έναν κωδικό έναντι αποθηκευμένου hash/salt (σταθερού χρόνου)."""
    computed, _ = hash_password(password, salt)
    return hmac.compare_digest(computed, expected_hash)


def _luhn_checksum(number: str) -> int:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10


def is_valid_amka(amka: str) -> bool:
    """Ελέγχει ότι ο ΑΜΚΑ είναι 11 ψηφία με έγκυρο ψηφίο ελέγχου (Luhn)."""
    if not amka or not amka.isdigit() or len(amka) != 11:
        return False
    return _luhn_checksum(amka) == 0


def generate_amka(ddmmyy: str, serial4: str) -> str:
    """Παράγει έγκυρο 11ψήφιο ΑΜΚΑ (6 ψηφία ημ/νίας + 4 σειριακά + 1 Luhn).

    Χρησιμοποιείται μόνο για παραγωγή ρεαλιστικών δεδομένων δοκιμής/seed.
    """
    if len(ddmmyy) != 6 or len(serial4) != 4:
        raise ValueError("Απαιτούνται 6 ψηφία ημερομηνίας και 4 σειριακά")
    first10 = ddmmyy + serial4
    check = (10 - _luhn_checksum(first10 + "0")) % 10
    return first10 + str(check)
