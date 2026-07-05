"""Επιχειρησιακή λογική αυθεντικοποίησης (UC001 Login, UC002 Logout).

Εφαρμόζει την απαίτηση ασφαλείας §4.2: κλείδωμα λογαριασμού μετά από
πολλαπλές αποτυχημένες προσπάθειες σύνδεσης.
"""
from __future__ import annotations

from ..model.entities import User
from ..model.user_repository import UserRepository
from ..util.security import hash_password, verify_password
from .exceptions import AuthenticationError, ValidationError

MAX_FAILED_ATTEMPTS = 5  # §4.2 — κλείδωμα μετά από 5 αποτυχίες


class AuthController:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
        self.current_user: User | None = None

    def register_user(self, username: str, password: str, role: str,
                      full_name: str = "", patient_id: int | None = None) -> User:
        """Βοηθητικό για δημιουργία λογαριασμού (seed/διαχείριση)."""
        username = (username or "").strip()
        if not username:
            raise ValidationError("Το username είναι υποχρεωτικό.")
        if not password:
            raise ValidationError("Ο κωδικός είναι υποχρεωτικός.")
        if self.user_repo.get_by_username(username) is not None:
            raise ValidationError("Το username χρησιμοποιείται ήδη.")
        pwd_hash, salt = hash_password(password)
        user = User(
            username=username, password_hash=pwd_hash, salt=salt, role=role,
            full_name=full_name, patient_id=patient_id,
        )
        return self.user_repo.add(user)

    def login(self, username: str, password: str) -> User:
        """UC001: Επιστρέφει τον χρήστη σε επιτυχία, αλλιώς AuthenticationError."""
        user = self.user_repo.get_by_username((username or "").strip())
        if user is None:
            # Δεν αποκαλύπτουμε αν υπάρχει ο χρήστης (αποφυγή enumeration).
            raise AuthenticationError("Λανθασμένα διαπιστευτήρια.")
        if user.locked:
            raise AuthenticationError(
                "Ο λογαριασμός είναι κλειδωμένος λόγω πολλαπλών αποτυχιών."
            )
        if not user.active:
            raise AuthenticationError("Ο λογαριασμός είναι ανενεργός.")

        if verify_password(password or "", user.salt, user.password_hash):
            if user.failed_attempts:
                user.failed_attempts = 0
                self.user_repo.update_security(user)
            self.current_user = user
            return user

        # Αποτυχία -> αύξηση μετρητή και πιθανό κλείδωμα.
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked = True
        self.user_repo.update_security(user)
        if user.locked:
            raise AuthenticationError(
                "Ο λογαριασμός κλειδώθηκε μετά από 5 αποτυχημένες προσπάθειες."
            )
        raise AuthenticationError("Λανθασμένα διαπιστευτήρια.")

    def logout(self) -> None:
        """UC002: Τερματισμός συνεδρίας."""
        self.current_user = None
