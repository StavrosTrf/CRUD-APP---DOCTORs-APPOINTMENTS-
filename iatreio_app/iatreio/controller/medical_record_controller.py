"""Επιχειρησιακή λογική ιατρικού ιστορικού & συνταγογράφησης.

Καλύπτει UC012 (Ενημέρωση Ιατρικού Ιστορικού) και UC013 (Συνταγογράφηση).
Κανόνας: εγγραφή επιτρέπεται μόνο αφού ο ασθενής έχει κάνει check-in
(ή το ραντεβού έχει ολοκληρωθεί). Η δημιουργία εγγραφής ολοκληρώνει το ραντεβού.
"""
from __future__ import annotations

from datetime import datetime

from ..model.entities import (
    MedicalRecord,
    STATUS_CHECKED_IN,
    STATUS_COMPLETED,
)
from ..model.medical_record_repository import MedicalRecordRepository
from ..model.appointment_repository import AppointmentRepository
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .validators import require_nonempty


class MedicalRecordController:
    def __init__(self, record_repo: MedicalRecordRepository,
                 appt_repo: AppointmentRepository) -> None:
        self.repo = record_repo
        self.appointments = appt_repo

    def add_record(self, doctor_id: int, appointment_id: int,
                   symptoms: str = "", diagnosis: str = "",
                   observations: str = "", prescription: str = "") -> MedicalRecord:
        appt = self.appointments.get_by_id(appointment_id)
        if appt is None:
            raise NotFoundError("Το ραντεβού δεν βρέθηκε.")
        if appt.status not in (STATUS_CHECKED_IN, STATUS_COMPLETED):
            raise BusinessRuleError(
                "Καταχώρηση ιστορικού επιτρέπεται μόνο μετά το check-in του ασθενούς."
            )
        # Απαιτείται τουλάχιστον διάγνωση (UC012).
        diagnosis = require_nonempty(diagnosis, "Διάγνωση")

        record = MedicalRecord(
            patient_id=appt.patient_id,
            appointment_id=appointment_id,
            doctor_id=doctor_id,
            symptoms=(symptoms or "").strip(),
            diagnosis=diagnosis,
            observations=(observations or "").strip(),
            prescription=(prescription or "").strip(),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        saved = self.repo.add(record)

        # Ολοκλήρωση ραντεβού μετά την καταχώρηση φακέλου.
        appt.status = STATUS_COMPLETED
        self.appointments.update(appt)
        return saved

    def get_history(self, patient_id: int) -> list[MedicalRecord]:
        """UC011 — Ανάκτηση & Προβολή Ιστορικού Ασθενούς."""
        return self.repo.list_for_patient(patient_id)

    def update_record(self, record_id: int, symptoms: str, diagnosis: str,
                      observations: str, prescription: str) -> MedicalRecord:
        record = self.repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Η εγγραφή δεν βρέθηκε.")
        record.diagnosis = require_nonempty(diagnosis, "Διάγνωση")
        record.symptoms = (symptoms or "").strip()
        record.observations = (observations or "").strip()
        record.prescription = (prescription or "").strip()
        self.repo.update(record)
        return record

    def delete_record(self, record_id: int) -> None:
        if self.repo.get_by_id(record_id) is None:
            raise NotFoundError("Η εγγραφή δεν βρέθηκε.")
        self.repo.delete(record_id)
