"""Unit tests για ιατρικό ιστορικό & συνταγογράφηση (UC012/UC013)."""
import pytest

from iatreio.controller.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from iatreio.model.entities import STATUS_COMPLETED


@pytest.fixture
def checked_in_appt(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="Παθολόγος", scheduled_at="2026-06-20 10:00",
    )
    ctx.appointments.check_in(a.id)
    return a


def test_add_record_success(ctx, doctor, checked_in_appt):
    rec = ctx.records.add_record(
        doctor_id=doctor.id, appointment_id=checked_in_appt.id,
        symptoms="Πυρετός", diagnosis="Ίωση",
        prescription="Παρακεταμόλη 500mg",
    )
    assert rec.id is not None
    assert rec.diagnosis == "Ίωση"
    # Το ραντεβού ολοκληρώνεται αυτόματα.
    appt = ctx.appointments.get_appointment(checked_in_appt.id)
    assert appt.status == STATUS_COMPLETED


def test_add_record_requires_checkin(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    # Δεν έχει γίνει check-in -> απορρίπτεται.
    with pytest.raises(BusinessRuleError):
        ctx.records.add_record(
            doctor_id=doctor.id, appointment_id=a.id, diagnosis="X"
        )


def test_add_record_requires_diagnosis(ctx, doctor, checked_in_appt):
    with pytest.raises(ValidationError):
        ctx.records.add_record(
            doctor_id=doctor.id, appointment_id=checked_in_appt.id,
            diagnosis="",
        )


def test_add_record_unknown_appointment(ctx, doctor):
    with pytest.raises(NotFoundError):
        ctx.records.add_record(
            doctor_id=doctor.id, appointment_id=9999, diagnosis="X"
        )


def test_get_history(ctx, doctor, patient, checked_in_appt):
    ctx.records.add_record(
        doctor_id=doctor.id, appointment_id=checked_in_appt.id,
        diagnosis="Διάγνωση 1",
    )
    history = ctx.records.get_history(patient.id)
    assert len(history) == 1
    assert history[0].diagnosis == "Διάγνωση 1"
    assert history[0].doctor_name == "Δρ. Τεστ"


def test_update_record(ctx, doctor, checked_in_appt):
    rec = ctx.records.add_record(
        doctor_id=doctor.id, appointment_id=checked_in_appt.id,
        diagnosis="Αρχική",
    )
    updated = ctx.records.update_record(
        rec.id, symptoms="νέα", diagnosis="Τελική",
        observations="obs", prescription="rx",
    )
    assert updated.diagnosis == "Τελική"
    assert updated.prescription == "rx"


def test_delete_record(ctx, doctor, patient, checked_in_appt):
    rec = ctx.records.add_record(
        doctor_id=doctor.id, appointment_id=checked_in_appt.id,
        diagnosis="Διάγνωση",
    )
    ctx.records.delete_record(rec.id)
    assert ctx.records.get_history(patient.id) == []
