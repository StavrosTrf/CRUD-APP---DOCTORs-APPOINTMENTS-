"""Κοινά fixtures για τα unit tests.

Κάθε test παίρνει καθαρή βάση SQLite στη μνήμη (:memory:) μέσω του AppContext,
ώστε να ελέγχεται όλο το wiring Model+Controller χωρίς GUI και χωρίς αρχείο.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iatreio.app_context import AppContext  # noqa: E402
from iatreio.model.entities import ROLE_DOCTOR, ROLE_SECRETARY  # noqa: E402
from iatreio.util.security import generate_amka  # noqa: E402


@pytest.fixture
def ctx():
    context = AppContext(":memory:")
    yield context
    context.close()


@pytest.fixture
def doctor(ctx):
    return ctx.auth.register_user(
        "doc", "secret", ROLE_DOCTOR, full_name="Δρ. Τεστ"
    )


@pytest.fixture
def secretary(ctx):
    return ctx.auth.register_user(
        "sec", "secret", ROLE_SECRETARY, full_name="Γραμματεία Τεστ"
    )


@pytest.fixture
def patient(ctx):
    return ctx.patients.create_patient(
        amka=generate_amka("010190", "1111"),
        first_name="Τεστ", last_name="Ασθενής",
        email="test@example.com", gdpr_consent=True,
    )


@pytest.fixture
def valid_amka():
    return generate_amka("311299", "4321")
