import pytest

from biovolt_simulator import __main__ as cli
from biovolt_simulator.config import SimulatorSettings
from biovolt_simulator.generator import TelemetryGenerator


def test_cli_flags_override_environment_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BIOVOLT_SIM_BACKEND_WS_URL", "ws://env.example/ws")
    monkeypatch.setenv("BIOVOLT_SIM_DEVICE_ID", "env-device")
    monkeypatch.setenv("BIOVOLT_SIM_CELL_ID", "env-cell")
    monkeypatch.setenv("BIOVOLT_SIM_DEVICE_TOKEN", "env-secret")
    monkeypatch.setenv("BIOVOLT_SIM_INTERVAL_SECONDS", "1.5")
    monkeypatch.setenv("BIOVOLT_SIM_SEED", "7")

    args = cli.parse_args(
        [
            "--backend-ws-url",
            "ws://cli.example/ws",
            "--device-id",
            "cli-device",
            "--cell-id",
            "cli-cell",
            "--token",
            "cli-secret",
            "--interval",
            "0.25",
            "--seed",
            "99",
            "--fault",
            "light_null",
            "--malformed-every",
            "3",
        ]
    )
    settings = cli.settings_from_args(args)

    assert settings == SimulatorSettings(
        backend_ws_url="ws://cli.example/ws",
        device_id="cli-device",
        cell_id="cli-cell",
        device_token="cli-secret",
        interval_seconds=0.25,
        seed=99,
    )
    assert args.fault == "light_null"
    assert args.malformed_every == 3


def test_cli_uses_environment_and_settings_defaults_without_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BIOVOLT_SIM_BACKEND_WS_URL", "ws://env.example/ws")
    monkeypatch.setenv("BIOVOLT_SIM_DEVICE_TOKEN", "env-secret")

    args = cli.parse_args([])
    settings = cli.settings_from_args(args)

    assert settings.backend_ws_url == "ws://env.example/ws"
    assert settings.device_id == "biovolt-sim-01"
    assert settings.cell_id == "cell-a"
    assert settings.device_token == "env-secret"
    assert settings.interval_seconds == 0.5
    assert settings.seed == 42
    assert args.fault is None
    assert args.malformed_every == 0


class _FrameSource:
    def __init__(self) -> None:
        self.calls = 0

    def next_frame(self, elapsed_seconds: float) -> dict[str, object]:
        self.calls += 1
        return {"sequence": self.calls, "elapsed": elapsed_seconds}


def test_malformed_every_removes_sequence_on_each_nth_frame() -> None:
    source = _FrameSource()
    wrapped = cli.MalformedFrameGenerator(source, malformed_every=3)

    first = wrapped.next_frame(0.0)
    second = wrapped.next_frame(0.5)
    third = wrapped.next_frame(1.0)
    fourth = wrapped.next_frame(1.5)

    assert first == {"sequence": 1, "elapsed": 0.0}
    assert second == {"sequence": 2, "elapsed": 0.5}
    assert third == {"elapsed": 1.0}
    assert fourth == {"sequence": 4, "elapsed": 1.5}


def test_malformed_every_zero_keeps_all_frames_intact() -> None:
    source = _FrameSource()
    wrapped = cli.MalformedFrameGenerator(source, malformed_every=0)

    assert wrapped.next_frame(0.0) == {"sequence": 1, "elapsed": 0.0}
    assert wrapped.next_frame(0.5) == {"sequence": 2, "elapsed": 0.5}


def test_malformed_every_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        cli.MalformedFrameGenerator(_FrameSource(), malformed_every=-1)


def test_startup_summary_contains_configuration_but_not_token() -> None:
    settings = SimulatorSettings(
        backend_ws_url="ws://localhost:8000/ws/device",
        device_id="biovolt-sim-01",
        cell_id="cell-a",
        device_token="super-secret-token",
        interval_seconds=0.5,
        seed=42,
    )

    assert cli.startup_summary(settings) == "\n".join(
        [
            "BioVolt simulator",
            "Device: biovolt-sim-01",
            "Cell: cell-a",
            "Target: ws://localhost:8000/ws/device",
            "Cadence: 0.5 s",
            "Seed: 42",
        ]
    )
    assert settings.device_token not in cli.startup_summary(settings)


def test_main_constructs_faulted_client_and_runs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class _Client:
        def __init__(self, settings: SimulatorSettings, *, generator: object) -> None:
            captured["settings"] = settings
            captured["generator"] = generator

        async def run(self) -> None:
            captured["ran"] = True

    original_client = cli.SimulatorClient
    original_asyncio_run = cli.asyncio.run

    def fake_run(awaitable: object) -> None:
        original_asyncio_run(awaitable)  # type: ignore[arg-type]

    cli.SimulatorClient = _Client  # type: ignore[assignment]
    cli.asyncio.run = fake_run  # type: ignore[assignment]
    try:
        cli.main(
            [
                "--backend-ws-url",
                "ws://localhost:8000/ws/device",
                "--token",
                "super-secret-token",
                "--fault",
                "temperature_null",
            ]
        )
    finally:
        cli.SimulatorClient = original_client
        cli.asyncio.run = original_asyncio_run

    settings = captured["settings"]
    generator = captured["generator"]
    assert isinstance(settings, SimulatorSettings)
    assert isinstance(generator, cli.MalformedFrameGenerator)
    assert generator.malformed_every == 0
    assert isinstance(generator.source, TelemetryGenerator)
    assert generator.source.fault == "temperature_null"
    assert captured["ran"] is True
    assert "super-secret-token" not in capsys.readouterr().out
