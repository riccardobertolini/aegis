"""Password hashing using Argon2id (argon2-cffi) — no external service."""
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

_ph = PasswordHasher(
    time_cost=3,       # iterations
    memory_cost=65536, # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Return Argon2id hash of the given password."""
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return True if password matches hashed.  Never raises."""
    try:
        return _ph.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def needs_rehash(hashed: str) -> bool:
    """True if the stored hash should be upgraded (params changed)."""
    return _ph.check_needs_rehash(hashed)
