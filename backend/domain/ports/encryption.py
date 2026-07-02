"""Encryption port — all crypto operations are local, air-gapped."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IEncryptionPort(ABC):
    """Port for symmetric encryption at rest.

    Implementations MUST:
    - Use a locally managed key (never sent over network)
    - Use authenticated encryption (e.g. AES-256-GCM via cryptography Fernet)
    - Raise EncryptionError on any failure
    """

    @abstractmethod
    def encrypt_bytes(self, plaintext: bytes) -> bytes:
        """Return encrypted + authenticated ciphertext."""

    @abstractmethod
    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        """Return decrypted plaintext; raise EncryptionError if tampered."""

    @abstractmethod
    def encrypt_str(self, plaintext: str) -> str:
        """Encrypt a UTF-8 string; return base64url-encoded ciphertext."""

    @abstractmethod
    def decrypt_str(self, ciphertext_b64: str) -> str:
        """Decrypt a base64url-encoded ciphertext; return UTF-8 string."""

    @abstractmethod
    def rotate_key(self, old_ciphertext: bytes, new_key_id: str) -> bytes:
        """Re-encrypt with a new key version (key rotation)."""

    @abstractmethod
    def key_id(self) -> str:
        """Return the identifier of the currently active key."""
