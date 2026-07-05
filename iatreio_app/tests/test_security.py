"""Unit tests για τις βοηθητικές συναρτήσεις ασφαλείας."""
from iatreio.util.security import (
    generate_amka,
    hash_password,
    is_valid_amka,
    verify_password,
)


def test_hash_is_not_plaintext():
    h, salt = hash_password("mypassword")
    assert h != "mypassword"
    assert len(salt) == 32  # 16 bytes hex


def test_same_password_different_salt_gives_different_hash():
    h1, s1 = hash_password("pw")
    h2, s2 = hash_password("pw")
    assert s1 != s2
    assert h1 != h2


def test_verify_password_correct():
    h, salt = hash_password("correct horse")
    assert verify_password("correct horse", salt, h) is True


def test_verify_password_wrong():
    h, salt = hash_password("correct horse")
    assert verify_password("wrong", salt, h) is False


def test_generated_amka_is_valid():
    amka = generate_amka("150385", "1234")
    assert len(amka) == 11
    assert is_valid_amka(amka) is True


def test_invalid_amka_wrong_length():
    assert is_valid_amka("123") is False


def test_invalid_amka_non_digit():
    assert is_valid_amka("1234567890a") is False


def test_invalid_amka_bad_checksum():
    valid = generate_amka("150385", "1234")
    # Αλλάζουμε το ψηφίο ελέγχου ώστε να χαλάσει το checksum.
    broken = valid[:-1] + str((int(valid[-1]) + 1) % 10)
    assert is_valid_amka(broken) is False
