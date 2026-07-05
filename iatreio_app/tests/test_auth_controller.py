"""Unit tests για την αυθεντικοποίηση (UC001/UC002, §4.2)."""
import pytest

from iatreio.controller.auth_controller import AuthController, MAX_FAILED_ATTEMPTS
from iatreio.controller.exceptions import AuthenticationError, ValidationError
from iatreio.model.entities import ROLE_DOCTOR


def test_register_and_login_success(ctx):
    ctx.auth.register_user("alice", "pw123", ROLE_DOCTOR, full_name="Alice")
    user = ctx.auth.login("alice", "pw123")
    assert user.username == "alice"
    assert user.role == ROLE_DOCTOR
    assert ctx.auth.current_user is user


def test_login_wrong_password(ctx):
    ctx.auth.register_user("bob", "pw123", ROLE_DOCTOR)
    with pytest.raises(AuthenticationError):
        ctx.auth.login("bob", "WRONG")


def test_login_unknown_user(ctx):
    with pytest.raises(AuthenticationError):
        ctx.auth.login("ghost", "x")


def test_duplicate_username_rejected(ctx):
    ctx.auth.register_user("carol", "pw", ROLE_DOCTOR)
    with pytest.raises(ValidationError):
        ctx.auth.register_user("carol", "other", ROLE_DOCTOR)


def test_empty_credentials_rejected(ctx):
    with pytest.raises(ValidationError):
        ctx.auth.register_user("", "pw", ROLE_DOCTOR)
    with pytest.raises(ValidationError):
        ctx.auth.register_user("dave", "", ROLE_DOCTOR)


def test_account_locks_after_max_attempts(ctx):
    ctx.auth.register_user("eve", "pw123", ROLE_DOCTOR)
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(AuthenticationError):
            ctx.auth.login("eve", "bad")
    # Η τελευταία αποτυχία κλειδώνει τον λογαριασμό.
    with pytest.raises(AuthenticationError):
        ctx.auth.login("eve", "bad")
    user = ctx.user_repo.get_by_username("eve")
    assert user.locked is True
    # Ακόμη και με σωστό κωδικό, ο κλειδωμένος λογαριασμός απορρίπτεται.
    with pytest.raises(AuthenticationError):
        ctx.auth.login("eve", "pw123")


def test_failed_counter_resets_after_success(ctx):
    ctx.auth.register_user("frank", "pw123", ROLE_DOCTOR)
    with pytest.raises(AuthenticationError):
        ctx.auth.login("frank", "bad")
    ctx.auth.login("frank", "pw123")
    user = ctx.user_repo.get_by_username("frank")
    assert user.failed_attempts == 0


def test_logout_clears_session(ctx):
    ctx.auth.register_user("grace", "pw123", ROLE_DOCTOR)
    ctx.auth.login("grace", "pw123")
    ctx.auth.logout()
    assert ctx.auth.current_user is None
