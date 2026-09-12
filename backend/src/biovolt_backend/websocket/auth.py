"""Authentication helpers for device WebSocket clients."""

import secrets

from starlette.datastructures import Headers


class DeviceAuthenticationError(ValueError):
    """Raised when a device WebSocket does not present valid credentials."""


def authenticate_device(headers: Headers, expected_token: str) -> str:
    """Validate device headers and return the authenticated device identifier."""

    device_id = headers.get("x-biovolt-device-id", "").strip()
    if not device_id:
        raise DeviceAuthenticationError("missing device id")

    authorization = headers.get("authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise DeviceAuthenticationError("missing bearer token")

    supplied_token = authorization[len(prefix) :]
    if not secrets.compare_digest(supplied_token, expected_token):
        raise DeviceAuthenticationError("invalid token")
    return device_id
