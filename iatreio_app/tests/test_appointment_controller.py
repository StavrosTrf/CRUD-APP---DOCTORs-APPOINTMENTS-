"""Unit tests για τη διαχείριση ραντεβού (UC003–UC008)."""
import pytest

from iatreio.controller.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from iatreio.model.entities import (
    STATUS_CANCELLED,
    STATUS_CHECKED_IN,
    STATUS_COMPLETED,
    STATUS_SCHEDULED,
)


def test_book_appointment_success(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="Παθολόγος", scheduled_at="2026-06-20 10:00",
    )
    assert a.id is not None
    assert a.status == STATUS_SCHEDULED
    assert a.scheduled_at == "2026-06-20 10:00"


def test_book_requires_gdpr_consent(ctx, doctor):
    from iatreio.util.security import generate_amka
    p = ctx.patients.create_patient(
        amka=generate_amka("050505", "9999"),
        first_name="No", last_name="Consent", gdpr_consent=False,
    )
    with pytest.raises(BusinessRuleError):
        ctx.appointments.book_appointment(
            patient_id=p.id, doctor_id=doctor.id,
            category="Παθολόγος", scheduled_at="2026-06-20 10:00",
        )


def test_book_unknown_patient(ctx, doctor):
    with pytest.raises(NotFoundError):
        ctx.appointments.book_appointment(
            patient_id=999, doctor_id=doctor.id,
            category="X", scheduled_at="2026-06-20 10:00",
        )


def test_book_unknown_doctor(ctx, patient):
    with pytest.raises(NotFoundError):
        ctx.appointments.book_appointment(
            patient_id=patient.id, doctor_id=999,
            category="X", scheduled_at="2026-06-20 10:00",
        )


def test_book_outside_working_hours(ctx, doctor, patient):
    with pytest.raises(ValidationError):
        ctx.appointments.book_appointment(
            patient_id=patient.id, doctor_id=doctor.id,
            category="X", scheduled_at="2026-06-20 23:30",
        )


def test_book_invalid_datetime(ctx, doctor, patient):
    with pytest.raises(ValidationError):
        ctx.appointments.book_appointment(
            patient_id=patient.id, doctor_id=doctor.id,
            category="X", scheduled_at="not-a-date",
        )


def test_double_booking_rejected(ctx, doctor, patient):
    ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    with pytest.raises(BusinessRuleError):
        ctx.appointments.book_appointment(
            patient_id=patient.id, doctor_id=doctor.id,
            category="Y", scheduled_at="2026-06-20 10:00",
        )


def test_reschedule_success(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    updated = ctx.appointments.reschedule(a.id, "2026-06-21 11:00")
    assert updated.scheduled_at == "2026-06-21 11:00"


def test_reschedule_conflict(ctx, doctor, patient):
    a1 = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="Y", scheduled_at="2026-06-20 12:00",
    )
    with pytest.raises(BusinessRuleError):
        ctx.appointments.reschedule(a1.id, "2026-06-20 12:00")


def test_check_in_changes_status(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    updated = ctx.appointments.check_in(a.id)
    assert updated.status == STATUS_CHECKED_IN


def test_check_in_twice_fails(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    ctx.appointments.check_in(a.id)
    with pytest.raises(BusinessRuleError):
        ctx.appointments.check_in(a.id)


def test_cancel_appointment(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    updated = ctx.appointments.cancel(a.id)
    assert updated.status == STATUS_CANCELLED


def test_cancelled_slot_can_be_rebooked(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    ctx.appointments.cancel(a.id)
    # Η ίδια ώρα είναι ξανά διαθέσιμη μετά την ακύρωση.
    a2 = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="Y", scheduled_at="2026-06-20 10:00",
    )
    assert a2.status == STATUS_SCHEDULED


def test_delete_appointment(ctx, doctor, patient):
    a = ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    ctx.appointments.delete_appointment(a.id)
    assert ctx.appointments.list_appointments() == []


def test_list_for_doctor_and_patient(ctx, doctor, patient):
    ctx.appointments.book_appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        category="X", scheduled_at="2026-06-20 10:00",
    )
    assert len(ctx.appointments.list_for_doctor(doctor.id)) == 1
    assert len(ctx.appointments.list_for_patient(patient.id)) == 1
    # joins: επιστρέφονται ονόματα
    appt = ctx.appointments.list_appointments()[0]
    assert appt.doctor_name == "Δρ. Τεστ"
    assert "Ασθενής" in appt.patient_name
