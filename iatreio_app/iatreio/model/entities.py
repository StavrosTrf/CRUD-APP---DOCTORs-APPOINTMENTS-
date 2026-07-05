"""Οντότητες πεδίου (Domain Entities).

Απλά αντικείμενα δεδομένων (dataclasses) που μεταφέρονται μεταξύ των επιπέδων
Model -> Controller -> View. Δεν περιέχουν λογική βάσης ή UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- Ρόλοι χρηστών (Actors του SRS, §2.3) ---
ROLE_PATIENT = "PATIENT"      # Ασθενής
ROLE_SECRETARY = "SECRETARY"  # Γραμματεία
ROLE_DOCTOR = "DOCTOR"        # Ιατρός
VALID_ROLES = {ROLE_PATIENT, ROLE_SECRETARY, ROLE_DOCTOR}

# --- Καταστάσεις ραντεβού ---
STATUS_SCHEDULED = "SCHEDULED"     # Προγραμματισμένο
STATUS_CHECKED_IN = "CHECKED_IN"   # Έφτασε / Σε αναμονή (UC008)
STATUS_COMPLETED = "COMPLETED"     # Ολοκληρωμένο
STATUS_CANCELLED = "CANCELLED"     # Ακυρωμένο
VALID_STATUSES = {
    STATUS_SCHEDULED,
    STATUS_CHECKED_IN,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
}


@dataclass
class User:
    """Λογαριασμός σύνδεσης στο σύστημα (UC001/UC002)."""
    id: int | None = None
    username: str = ""
    password_hash: str = ""
    salt: str = ""
    role: str = ROLE_PATIENT
    full_name: str = ""
    patient_id: int | None = None  # Σύνδεση λογαριασμού ασθενούς με φάκελο
    active: bool = True
    failed_attempts: int = 0
    locked: bool = False


@dataclass
class Patient:
    """Φάκελος ασθενούς."""
    id: int | None = None
    amka: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    email: str = ""
    date_of_birth: str = ""        # μορφή YYYY-MM-DD
    gdpr_consent: bool = False     # Έγκριση GDPR (UC010)
    created_at: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()


@dataclass
class Appointment:
    """Ραντεβού (UC003–UC008)."""
    id: int | None = None
    patient_id: int = 0
    doctor_id: int = 0
    category: str = ""             # Κατηγορία εξέτασης
    scheduled_at: str = ""         # μορφή YYYY-MM-DD HH:MM
    status: str = STATUS_SCHEDULED
    notes: str = ""
    # Πεδία ανάγνωσης (joins) — γεμίζουν προαιρετικά από το repository
    patient_name: str = ""
    doctor_name: str = ""


@dataclass
class MedicalRecord:
    """Εγγραφή ιατρικού ιστορικού / συνταγογράφηση (UC012/UC013)."""
    id: int | None = None
    patient_id: int = 0
    appointment_id: int | None = None
    doctor_id: int = 0
    symptoms: str = ""
    diagnosis: str = ""
    observations: str = ""
    prescription: str = ""         # Φαρμακευτική αγωγή
    created_at: str = ""
    doctor_name: str = ""
