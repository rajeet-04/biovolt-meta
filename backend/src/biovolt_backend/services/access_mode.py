from fastapi import HTTPException, Request

from biovolt_backend.models.capabilities import AccessMode, Capabilities


def resolve_access_mode(request: Request) -> AccessMode:
    value = request.headers.get("X-BioVolt-Access-Mode", "operator")
    if value not in ("operator", "public_read_only"):
        raise HTTPException(400, "invalid access mode")
    return value


def capabilities(request: Request) -> Capabilities:
    mode = resolve_access_mode(request)
    operator = mode == "operator"
    return Capabilities(
        access_mode=mode,
        can_control=operator,
        can_manage_experiments=operator,
        can_manage_calibration=operator,
    )
