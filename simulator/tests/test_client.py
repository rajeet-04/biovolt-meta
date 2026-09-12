import asyncio
import json
from unittest.mock import Mock

import pytest
import websockets

from biovolt_simulator.client import SimulatorClient, device_headers, reconnect_delay
from biovolt_simulator.config import SimulatorSettings


def _settings() -> SimulatorSettings:
    return SimulatorSettings(
        backend_ws_url="ws://localhost:8000/ws/device",
        device_id="sim-17",
        cell_id="cell-b",
        device_token="secret-token",
    )


def test_device_headers_use_exact_protocol_names() -> None:
    assert device_headers(_settings()) == {
        "X-BioVolt-Device-ID": "sim-17",
        "Authorization": "Bearer secret-token",
    }


@pytest.mark.parametrize(
    ("attempt", "expected"),
    [(0, 1.0), (1, 2.0), (2, 4.0), (3, 8.0), (4, 10.0), (5, 10.0), (20, 10.0)],
)
def test_reconnect_delay_is_bounded_exponential(attempt: int, expected: float) -> None:
    assert reconnect_delay(attempt) == expected


class _Context:
    def __init__(
        self, value: object = None, error: BaseException | None = None
    ) -> None:
        self.value = value
        self.error = error

    async def __aenter__(self) -> object:
        if self.error is not None:
            raise self.error
        return self.value

    async def __aexit__(self, *_args: object) -> None:
        return None


class _RecordingGenerator:
    def __init__(self) -> None:
        self.elapsed: list[float] = []

    def next_frame(self, elapsed_seconds: float) -> dict[str, object]:
        self.elapsed.append(elapsed_seconds)
        return {"sequence": len(self.elapsed), "elapsed": elapsed_seconds}


class _RecordingWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, message: str) -> None:
        self.sent.append(message)


class _DisconnectingWebSocket(_RecordingWebSocket):
    async def send(self, message: str) -> None:
        await super().send(message)
        if len(self.sent) == 2:
            raise websockets.WebSocketException("connection closed")


@pytest.mark.asyncio
async def test_client_reconnects_and_preserves_cadence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings()
    generator = _RecordingGenerator()
    websocket = _RecordingWebSocket()
    connect_calls: list[tuple[str, dict[str, str]]] = []
    connect_results = iter(
        [_Context(error=OSError("disconnected")), _Context(value=websocket)]
    )

    def connect(url: str, *, additional_headers: dict[str, str]) -> _Context:
        connect_calls.append((url, additional_headers))
        return next(connect_results)

    sleep_calls: list[float] = []

    async def sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        if len(sleep_calls) == 2:
            raise asyncio.CancelledError

    monotonic_values = iter([100.0, 100.5])
    monkeypatch.setattr("biovolt_simulator.client.websockets.connect", connect)
    monkeypatch.setattr("biovolt_simulator.client.asyncio.sleep", sleep)
    monkeypatch.setattr(
        "biovolt_simulator.client.monotonic", lambda: next(monotonic_values)
    )

    with pytest.raises(asyncio.CancelledError):
        await SimulatorClient(settings, generator=generator).run()

    assert connect_calls == [
        (settings.backend_ws_url, device_headers(settings)),
        (settings.backend_ws_url, device_headers(settings)),
    ]
    assert sleep_calls == [1.0, settings.interval_seconds]
    assert generator.elapsed == [0.5]
    assert [json.loads(message) for message in websocket.sent] == [
        {"sequence": 1, "elapsed": 0.5}
    ]


@pytest.mark.asyncio
async def test_client_propagates_cancellation_from_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect = Mock(return_value=_Context(error=asyncio.CancelledError()))
    monkeypatch.setattr("biovolt_simulator.client.websockets.connect", connect)

    with pytest.raises(asyncio.CancelledError):
        await SimulatorClient(_settings()).run()


@pytest.mark.asyncio
async def test_client_preserves_elapsed_origin_across_reconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings()
    generator = _RecordingGenerator()
    first_websocket = _DisconnectingWebSocket()
    second_websocket = _RecordingWebSocket()
    connect_results = iter(
        [_Context(value=first_websocket), _Context(value=second_websocket)]
    )

    def connect(_url: str, *, additional_headers: dict[str, str]) -> _Context:
        del additional_headers
        return next(connect_results)

    sleep_calls: list[float] = []

    async def sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        if len(sleep_calls) == 3:
            raise asyncio.CancelledError

    monotonic_values = iter([100.0, 100.0, 100.5, 100.75, 101.0])
    monkeypatch.setattr("biovolt_simulator.client.websockets.connect", connect)
    monkeypatch.setattr("biovolt_simulator.client.asyncio.sleep", sleep)
    monkeypatch.setattr(
        "biovolt_simulator.client.monotonic", lambda: next(monotonic_values)
    )

    with pytest.raises(asyncio.CancelledError):
        await SimulatorClient(settings, generator=generator).run()

    first_frames = [json.loads(message) for message in first_websocket.sent]
    second_frames = [json.loads(message) for message in second_websocket.sent]
    assert first_frames[0]["elapsed"] == 0.0
    assert second_frames[0]["elapsed"] > first_frames[-1]["elapsed"]
    assert generator.elapsed == [0.0, 0.5, 0.75]
    assert sleep_calls == [settings.interval_seconds, 1.0, settings.interval_seconds]
