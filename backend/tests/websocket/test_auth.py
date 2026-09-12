import pytest
from starlette.datastructures import Headers

from biovolt_backend.websocket.auth import (
    DeviceAuthenticationError,
    authenticate_device,
)


def _headers(**values: str) -> Headers:
    return Headers(values)


def test_valid_device_auth_returns_device_id() -> None:
    headers = _headers(
        **{
            "x-biovolt-device-id": "biovolt-01",
            "authorization": "Bearer secret-12345",
        },
    )
    assert authenticate_device(headers, "secret-12345") == "biovolt-01"


@pytest.mark.parametrize(
    ("headers", "message"),
    [
        (_headers(authorization="Bearer secret-12345"), "missing device id"),
        (_headers(**{"x-biovolt-device-id": "biovolt-01"}), "missing bearer token"),
        (
            _headers(
                **{
                    "x-biovolt-device-id": "biovolt-01",
                    "authorization": "Basic secret-12345",
                },
            ),
            "missing bearer token",
        ),
        (
            _headers(
                **{
                    "x-biovolt-device-id": "biovolt-01",
                    "authorization": "Bearer wrong-token",
                },
            ),
            "invalid token",
        ),
        (
            _headers(
                **{
                    "x-biovolt-device-id": "   ",
                    "authorization": "Bearer secret-12345",
                },
            ),
            "missing device id",
        ),
    ],
)
def test_invalid_device_auth_is_rejected(headers: Headers, message: str) -> None:
    with pytest.raises(DeviceAuthenticationError, match=message):
        authenticate_device(headers, "secret-12345")
