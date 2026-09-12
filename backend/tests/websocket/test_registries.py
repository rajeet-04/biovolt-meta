import asyncio
from datetime import UTC, datetime

from biovolt_backend.websocket.dashboard_hub import DashboardHub
from biovolt_backend.websocket.device_registry import DeviceRegistry


class FakeWebSocket:
    def __init__(self, *, fails: bool = False) -> None:
        self.fails = fails
        self.payloads: list[dict[str, object]] = []

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.fails:
            raise RuntimeError("socket closed")
        self.payloads.append(payload)


def test_device_registry_reconnect_and_matching_disconnect() -> None:
    registry = DeviceRegistry()
    old_socket = FakeWebSocket()
    new_socket = FakeWebSocket()

    registry.connect("biovolt-01", old_socket)
    registry.connect("biovolt-01", new_socket)
    registry.disconnect("biovolt-01", old_socket)
    assert registry.connected_device_ids() == ["biovolt-01"]

    registry.disconnect("biovolt-01", new_socket)
    assert registry.connected_device_ids() == []


def test_device_registry_tracks_latest_telemetry_timestamp() -> None:
    registry = DeviceRegistry()
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    registry.mark_telemetry("biovolt-01", received_at)

    assert registry.latest_telemetry_at("biovolt-01") == received_at
    assert registry.latest_telemetry_at("missing") is None


async def test_dashboard_broadcast_removes_failed_socket_and_reaches_healthy_socket() -> None:
    hub = DashboardHub()
    failed = FakeWebSocket(fails=True)
    healthy = FakeWebSocket()
    hub.connect(failed)
    hub.connect(healthy)

    payload = {"sequence": 3}
    await hub.broadcast_json(payload)

    assert healthy.payloads == [payload]
    await hub.broadcast_json({"sequence": 4})
    assert healthy.payloads == [payload, {"sequence": 4}]


async def test_dashboard_broadcast_isolates_async_send_failures() -> None:
    hub = DashboardHub()
    failed = FakeWebSocket(fails=True)
    healthy = FakeWebSocket()
    hub.connect(failed)
    hub.connect(healthy)

    await hub.broadcast_json({"sequence": 8})

    assert healthy.payloads == [{"sequence": 8}]


class NeverCompletesWebSocket:
    async def send_json(self, payload: dict[str, object]) -> None:
        await asyncio.Event().wait()


async def test_dashboard_broadcast_is_bounded_for_stalled_client() -> None:
    hub = DashboardHub()
    stalled = NeverCompletesWebSocket()
    healthy = FakeWebSocket()
    hub.connect(stalled)
    hub.connect(healthy)

    await asyncio.wait_for(hub.broadcast_json({"sequence": 9}), timeout=0.5)

    assert healthy.payloads == [{"sequence": 9}]
    await hub.broadcast_json({"sequence": 10})
    assert healthy.payloads == [{"sequence": 9}, {"sequence": 10}]
