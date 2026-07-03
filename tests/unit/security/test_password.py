"""Unit tests: Argon2id password hashing."""
from backend.infrastructure.security.password import hash_password, needs_rehash, verify_password


def test_hash_returns_string():
    h = hash_password("secret")
    assert isinstance(h, str)
    assert h.startswith("$argon2id$")


def test_verify_correct_password():
    h = hash_password("correct-horse")
    assert verify_password("correct-horse", h) is True


def test_verify_wrong_password():
    h = hash_password("correct-horse")
    assert verify_password("wrong", h) is False


def test_no_two_hashes_are_identical():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # different salts


def test_needs_rehash_fresh_hash():
    h = hash_password("pw")
    assert needs_rehash(h) is False
