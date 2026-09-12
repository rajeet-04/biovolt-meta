"""Command-line entrypoint for the BioVolt device simulator."""

from __future__ import annotations

import argparse
import asyncio
from typing import Protocol

from .client import SimulatorClient
from .config import SimulatorSettings
from .faults import SUPPORTED_FAULTS
from .generator import TelemetryGenerator


class _FrameSource(Protocol):
    def next_frame(self, elapsed_seconds: float) -> dict[str, object]: ...


class MalformedFrameGenerator:
    """Remove ``sequence`` from every Nth frame for rejection testing."""

    def __init__(self, source: _FrameSource, *, malformed_every: int = 0) -> None:
        if malformed_every < 0:
            raise ValueError("malformed_every must be non-negative")
        self.source = source
        self.malformed_every = malformed_every
        self._frame_count = 0

    def next_frame(self, elapsed_seconds: float) -> dict[str, object]:
        self._frame_count += 1
        frame = dict(self.source.next_frame(elapsed_seconds))
        if self.malformed_every > 0 and self._frame_count % self.malformed_every == 0:
            frame.pop("sequence", None)
        return frame


def build_parser() -> argparse.ArgumentParser:
    """Build the simulator command-line parser."""

    parser = argparse.ArgumentParser(description="Run the BioVolt device simulator")
    parser.add_argument("--backend-ws-url")
    parser.add_argument("--device-id")
    parser.add_argument("--cell-id")
    parser.add_argument("--token")
    parser.add_argument("--interval", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--fault", choices=sorted(SUPPORTED_FAULTS))
    parser.add_argument("--malformed-every", type=int, default=0)
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI flags, leaving omitted settings to environment/defaults."""

    return build_parser().parse_args(argv)


def settings_from_args(args: argparse.Namespace) -> SimulatorSettings:
    """Load settings and apply only the values explicitly supplied by the CLI."""

    overrides = {
        "backend_ws_url": args.backend_ws_url,
        "device_id": args.device_id,
        "cell_id": args.cell_id,
        "device_token": args.token,
        "interval_seconds": args.interval,
        "seed": args.seed,
    }
    return SimulatorSettings(
        **{key: value for key, value in overrides.items() if value is not None}
    )


def build_frame_generator(
    settings: SimulatorSettings,
    *,
    fault: str | None,
    malformed_every: int,
) -> MalformedFrameGenerator:
    """Compose the deterministic generator with optional fault transformations."""

    generator = TelemetryGenerator(
        seed=settings.seed,
        device_id=settings.device_id,
        cell_id=settings.cell_id,
        start_sequence=settings.start_sequence,
        fault=fault,
    )
    return MalformedFrameGenerator(generator, malformed_every=malformed_every)


def startup_summary(settings: SimulatorSettings) -> str:
    """Return the token-safe startup summary shown by the CLI."""

    return "\n".join(
        [
            "BioVolt simulator",
            f"Device: {settings.device_id}",
            f"Cell: {settings.cell_id}",
            f"Target: {settings.backend_ws_url}",
            f"Cadence: {settings.interval_seconds} s",
            f"Seed: {settings.seed}",
        ]
    )


def main(argv: list[str] | None = None) -> None:
    """Parse settings, print a safe summary, and run the simulator client."""

    args = parse_args(argv)
    settings = settings_from_args(args)
    generator = build_frame_generator(
        settings,
        fault=args.fault,
        malformed_every=args.malformed_every,
    )
    print(startup_summary(settings))
    asyncio.run(SimulatorClient(settings, generator=generator).run())


if __name__ == "__main__":  # pragma: no cover
    main()
