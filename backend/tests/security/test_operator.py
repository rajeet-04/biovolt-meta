from argon2 import PasswordHasher

from biovolt_backend.config import Settings
from biovolt_backend.security.operator import OperatorAuthenticator


def test_operator_authenticator_verifies_only_matching_pin() -> None:
    authenticator = OperatorAuthenticator(PasswordHasher().hash("2468"))

    assert authenticator.verify_pin("2468") is True
    assert authenticator.verify_pin("0000") is False
    assert OperatorAuthenticator(None).verify_pin("2468") is False


def test_operator_pin_hash_is_not_in_settings_repr() -> None:
    settings = Settings(operator_pin_hash=PasswordHasher().hash("2468"))
    assert settings.operator_pin_hash not in repr(settings)
