"""Επιχειρησιακή λογική ραντεβού.

Καλύπτει:
  UC003/UC004 — Κράτηση & Προγραμματισμός Ραντεβού
  UC006       — Επαναπρογραμματισμός
  UC008       — Check-in
και τους κανόνες: έλεγχος διαθεσιμότητας ιατρού (όχι double-booking, UC005),
έγκυρη ώρα εντός ωραρίου, υποχρεωτική συγκατάθεση GDPR πριν την κράτηση.
"""
from __future__ import annotations

from ..model.entities import (
    Appointment,
    ROLE_DOCTOR,
    STATUS_CANCELLED,
    STATUS_CHECKED_IN,
    STATUS_COMPLETED,
    STATUS_SCHEDULED,
)
from ..model.appointment_repository import AppointmentRepository
from ..model.patient_repository import PatientRepository
from ..model.user_repository import UserRepository
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .validators import (
    parse_datetime,
    require_nonempty,
    validate_within_working_hours,
)


class AppointmentController:
    def __init__(self, appt_repo: AppointmentRepository,
                 patient_repo: PatientRepository,
                 user_repo: UserRepository) -> None:
        self.repo = appt_repo
        self.patients = patient_repo
        self.users = user_repo

    # --- Βοηθητικά ---
    def _ensure_patient(self, patient_id: int):
        patient = self.patients.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Ο ασθενής δεν βρέθηκε.")
        return patient

    def _ensure_doctor(self, doctor_id: int):
        doctor = self.users.get_by_id(doctor_id)
        if doctor is None or doctor.role != ROLE_DOCTOR:
            raise NotFoundError("Ο ιατρός δεν βρέθηκε.")
        return doctor

    # --- UC003/UC004: Κράτηση ---
    def book_appointment(self, patient_id: int, doctor_id: int,
                         category: str, scheduled_at: str,
                         notes: str = "") -> Appointment:
        patient = self._ensure_patient(patient_id)
        self._ensure_doctor(doctor_id)
        category = require_nonempty(category, "Κατηγορία εξέτασης")

        # UC010 — δεν επιτρέπεται κράτηση χωρίς συγκατάθεση GDPR.
        if not patient.gdpr_consent:
            raise BusinessRuleError(
                "Απαιτείται συγκατάθεση GDPR του ασθενούς πριν την κράτηση."
            )

        dt = parse_datetime(scheduled_at)
        validate_within_working_hours(dt)
        normalized = dt.strftime("%Y-%m-%d %H:%M")

        # UC005 — έλεγχος διαθεσιμότητας ιατρού (όχι double-booking).
        if self.repo.find_conflict(doctor_id, normalized) is not None:
            raise BusinessRuleError(
                "Ο ιατρός έχει ήδη ραντεβού τη συγκεκριμένη ώρα."
            )

        appt = Appointment(
            patient_id=patient_id, doctor_id=doctor_id, category=category,
            scheduled_at=normalized, status=STATUS_SCHEDULED,
            notes=(notes or "").strip(),
        )
        return self.repo.add(appt)

    # --- Read ---
    def get_appointment(self, appt_id: int) -> Appointment:
        appt = self.repo.get_by_id(appt_id)
        if appt is None:
            raise NotFoundError("Το ραντεβού δεν βρέθηκε.")
        return appt

    def list_appointments(self) -> list[Appointment]:
        return self.repo.list_all()

    def list_for_patient(self, patient_id: int) -> list[Appointment]:
        return self.repo.list_for_patient(patient_id)

    def list_for_doctor(self, doctor_id: int) -> list[Appointment]:
        return self.repo.list_for_doctor(doctor_id)

    # --- UC006: Επαναπρογραμματισμός ---
    def reschedule(self, appt_id: int, new_datetime: str) -> Appointment:
        appt = self.get_appointment(appt_id)
        if appt.status in (STATUS_CANCELLED, STATUS_COMPLETED):
            raise BusinessRuleError(
                "Δεν επιτρέπεται επαναπρογραμματισμός ακυρωμένου ή "
                "ολοκληρωμένου ραντεβού."
            )
        dt = parse_datetime(new_datetime)
        validate_within_working_hours(dt)
        normalized = dt.strftime("%Y-%m-%d %H:%M")

        conflict = self.repo.find_conflict(
            appt.doctor_id, normalized, exclude_id=appt.id
        )
        if conflict is not None:
            raise BusinessRuleError(
                "Ο ιατρός έχει ήδη ραντεβού τη συγκεκριμένη ώρα."
            )
        appt.scheduled_at = normalized
        appt.status = STATUS_SCHEDULED
        self.repo.update(appt)
        return appt

    # --- UC008: Check-in ---
    def check_in(self, appt_id: int) -> Appointment:
        appt = self.get_appointment(appt_id)
        if appt.status != STATUS_SCHEDULED:
            raise BusinessRuleError(
                "Check-in επιτρέπεται μόνο σε προγραμματισμένο ραντεβού."
            )
        appt.status = STATUS_CHECKED_IN
        self.repo.update(appt)
        return appt

    def mark_completed(self, appt_id: int) -> Appointment:
        appt = self.get_appointment(appt_id)
        appt.status = STATUS_COMPLETED
        self.repo.update(appt)
        return appt

    # --- Ακύρωση (status) & Διαγραφή (CRUD-Delete) ---
    def cancel(self, appt_id: int) -> Appointment:
        appt = self.get_appointment(appt_id)
        if appt.status == STATUS_COMPLETED:
            raise BusinessRuleError(
                "Δεν επιτρέπεται ακύρωση ολοκληρωμένου ραντεβού."
            )
        appt.status = STATUS_CANCELLED
        self.repo.update(appt)
        return appt

    def delete_appointment(self, appt_id: int) -> None:
        self.get_appointment(appt_id)
        self.repo.delete(appt_id)
