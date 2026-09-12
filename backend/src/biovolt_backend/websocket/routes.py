"""WebSocket endpoints for authenticated devices and read-only dashboards."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError

from biovolt_backend.commands.schemas import DeviceAck
from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.services.telemetry_service import TelemetryRejected
from biovolt_backend.websocket.auth import DeviceAuthenticationError, authenticate_device

router = APIRouter()


def _error_payload() -> dict[str, str]:
    return {"error": "invalid telemetry frame"}


@router.websocket("/ws/device")
async def device_websocket(websocket: WebSocket) -> None:
    """Receive authenticated raw telemetry and fan out processed frames."""

    try:
        device_id = authenticate_device(
            websocket.headers,
            websocket.app.state.settings.device_shared_token,
        )
    except DeviceAuthenticationError:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    registry = websocket.app.state.device_registry
    registry.connect(device_id, websocket)
    await websocket.app.state.command_dispatcher.dispatch_pending_for_device(device_id)
    try:
        while True:
            try:
                frame = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                payload = json.loads(frame)
                if not isinstance(payload, dict):
                    raise ValueError("device frame must be an object")
                schema_version = payload.get("schema_version")
                if schema_version == "device-ack.v1":
                    validate_payload("device-ack.v1.schema.json", payload)
                    ack = DeviceAck.model_validate(payload)
                    if ack.device_id != device_id:
                        raise ValueError("ack device id mismatch")
                    await websocket.app.state.command_service.apply_ack(ack)
                elif schema_version == 1:
                    await websocket.app.state.telemetry_service.handle_raw(
                        payload,
                        authenticated_device_id=device_id,
                        received_at=datetime.now(UTC),
                    )
                else:
                    raise ValueError("unknown device frame schema")
            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
                TelemetryRejected,
                JsonSchemaValidationError,
                ValidationError,
            ):
                await websocket.send_json(_error_payload())
    finally:
        registry.disconnect(device_id, websocket)


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """Keep a read-only dashboard socket alive for telemetry fanout."""

    await websocket.accept()
    hub = websocket.app.state.dashboard_hub
    hub.connect(websocket)
    try:
        while True:
            # Phase 1 dashboards cannot issue commands; consume and ignore all
            # client frames so a client cannot block its own connection.
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    finally:
        hub.disconnect(websocket)
