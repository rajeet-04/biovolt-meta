"""Argon2-backed operator PIN verification."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class OperatorAuthenticator:
    """Verify a plaintext PIN against an environment-provided Argon2 hash."""

    def __init__(self, pin_hash: str | None) -> None:
        self._pin_hash = pin_hash
        self._hasher = PasswordHasher()

    def verify_pin(self, pin: str) -> bool:
        if not self._pin_hash or not isinstance(pin, str):
            return False
        try:
            return self._hasher.verify(self._pin_hash, pin)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False
