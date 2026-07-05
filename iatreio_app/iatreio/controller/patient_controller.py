"""Επιχειρησιακή λογική διαχείρισης ασθενών (CRUD).

Καλύπτει επικύρωση στοιχείων (σχετίζεται με UC009 — Επαλήθευση Στοιχείων)
και τήρηση συγκατάθεσης GDPR (UC010).
"""
from __future__ import annotations

from datetime import datetime

from ..model.entities import Patient
from ..model.patient_repository import PatientRepository
from .exceptions import BusinessRuleError, NotFoundError, ValidationError
from .validators import require_nonempty, validate_amka, validate_email


class PatientController:
    def __init__(self, patient_repo: PatientRepository) -> None:
        self.repo = patient_repo

    def create_patient(self, amka: str, first_name: str, last_name: str,
                       phone: str = "", email: str = "",
                       date_of_birth: str = "",
                       gdpr_consent: bool = False) -> Patient:
        amka = validate_amka(amka)
        first_name = require_nonempty(first_name, "Όνομα")
        last_name = require_nonempty(last_name, "Επώνυμο")
        email = validate_email(email)

        if self.repo.get_by_amka(amka) is not None:
            raise BusinessRuleError("Υπάρχει ήδη ασθενής με αυτόν τον ΑΜΚΑ.")

        patient = Patient(
            amka=amka, first_name=first_name, last_name=last_name,
            phone=(phone or "").strip(), email=email,
            date_of_birth=(date_of_birth or "").strip(),
            gdpr_consent=bool(gdpr_consent),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        return self.repo.add(patient)

    def get_patient(self, patient_id: int) -> Patient:
        patient = self.repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Ο ασθενής δεν βρέθηκε.")
        return patient

    def list_patients(self) -> list[Patient]:
        return self.repo.list_all()

    def search_patients(self, term: str) -> list[Patient]:
        term = (term or "").strip()
        if not term:
            return self.repo.list_all()
        return self.repo.search(term)

    def update_patient(self, patient_id: int, amka: str, first_name: str,
                       last_name: str, phone: str = "", email: str = "",
                       date_of_birth: str = "",
                       gdpr_consent: bool = False) -> Patient:
        patient = self.get_patient(patient_id)
        amka = validate_amka(amka)
        first_name = require_nonempty(first_name, "Όνομα")
        last_name = require_nonempty(last_name, "Επώνυμο")
        email = validate_email(email)

        existing = self.repo.get_by_amka(amka)
        if existing is not None and existing.id != patient_id:
            raise BusinessRuleError("Ο ΑΜΚΑ ανήκει σε άλλον ασθενή.")

        patient.amka = amka
        patient.first_name = first_name
        patient.last_name = last_name
        patient.phone = (phone or "").strip()
        patient.email = email
        patient.date_of_birth = (date_of_birth or "").strip()
        patient.gdpr_consent = bool(gdpr_consent)
        self.repo.update(patient)
        return patient

    def set_gdpr_consent(self, patient_id: int, consent: bool) -> Patient:
        """UC010 — καταγραφή/ανάκληση συγκατάθεσης GDPR."""
        patient = self.get_patient(patient_id)
        patient.gdpr_consent = bool(consent)
        self.repo.update(patient)
        return patient

    def delete_patient(self, patient_id: int) -> None:
        self.get_patient(patient_id)  # σηκώνει NotFoundError αν δεν υπάρχει
        self.repo.delete(patient_id)
