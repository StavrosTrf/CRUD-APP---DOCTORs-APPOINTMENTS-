"""Unit tests για τη διαχείριση ασθενών (CRUD)."""
import pytest

from iatreio.controller.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)


def test_create_patient_success(ctx, valid_amka):
    p = ctx.patients.create_patient(
        amka=valid_amka, first_name="Γιώργος", last_name="Παππάς",
        email="g@example.com", gdpr_consent=True,
    )
    assert p.id is not None
    assert p.full_name == "Παππάς Γιώργος"
    assert p.gdpr_consent is True


def test_create_patient_invalid_amka(ctx):
    with pytest.raises(ValidationError):
        ctx.patients.create_patient(
            amka="123", first_name="A", last_name="B"
        )


def test_create_patient_missing_name(ctx, valid_amka):
    with pytest.raises(ValidationError):
        ctx.patients.create_patient(
            amka=valid_amka, first_name="", last_name="B"
        )


def test_create_patient_invalid_email(ctx, valid_amka):
    with pytest.raises(ValidationError):
        ctx.patients.create_patient(
            amka=valid_amka, first_name="A", last_name="B",
            email="not-an-email",
        )


def test_duplicate_amka_rejected(ctx, valid_amka):
    ctx.patients.create_patient(amka=valid_amka, first_name="A", last_name="B")
    with pytest.raises(BusinessRuleError):
        ctx.patients.create_patient(
            amka=valid_amka, first_name="C", last_name="D"
        )


def test_read_and_list(ctx, valid_amka):
    p = ctx.patients.create_patient(
        amka=valid_amka, first_name="A", last_name="B"
    )
    fetched = ctx.patients.get_patient(p.id)
    assert fetched.amka == valid_amka
    assert len(ctx.patients.list_patients()) == 1


def test_get_missing_patient_raises(ctx):
    with pytest.raises(NotFoundError):
        ctx.patients.get_patient(9999)


def test_update_patient(ctx, valid_amka):
    p = ctx.patients.create_patient(
        amka=valid_amka, first_name="A", last_name="B"
    )
    updated = ctx.patients.update_patient(
        p.id, amka=valid_amka, first_name="Αλλαγμένο", last_name="Επώνυμο",
        phone="6911111111",
    )
    assert updated.first_name == "Αλλαγμένο"
    assert ctx.patients.get_patient(p.id).phone == "6911111111"


def test_delete_patient(ctx, valid_amka):
    p = ctx.patients.create_patient(
        amka=valid_amka, first_name="A", last_name="B"
    )
    ctx.patients.delete_patient(p.id)
    assert ctx.patients.list_patients() == []
    with pytest.raises(NotFoundError):
        ctx.patients.get_patient(p.id)


def test_search_patient(ctx):
    from iatreio.util.security import generate_amka
    ctx.patients.create_patient(
        amka=generate_amka("010180", "0001"),
        first_name="Μαρία", last_name="Νικολάου",
    )
    ctx.patients.create_patient(
        amka=generate_amka("020280", "0002"),
        first_name="Πέτρος", last_name="Ιωάννου",
    )
    results = ctx.patients.search_patients("Νικολ")
    assert len(results) == 1
    assert results[0].last_name == "Νικολάου"


def test_set_gdpr_consent(ctx, valid_amka):
    p = ctx.patients.create_patient(
        amka=valid_amka, first_name="A", last_name="B", gdpr_consent=False
    )
    assert p.gdpr_consent is False
    updated = ctx.patients.set_gdpr_consent(p.id, True)
    assert updated.gdpr_consent is True
