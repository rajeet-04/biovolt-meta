"""Deterministic raw telemetry generation for a simulated BioVolt device."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class SimulatorState:
    """The sequence and uptime of the most recently emitted frame."""

    sequence: int
    uptime_ms: int


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "shared" / "schemas").is_dir():
            return parent
    raise RuntimeError("could not locate the repository shared schema directory")


@cache
def _telemetry_validator() -> Draft202012Validator:
    schema_path = (
        _repository_root() / "shared" / "schemas" / "device-telemetry.v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_telemetry_frame(payload: dict[str, object]) -> None:
    """Validate a generated frame against the canonical Phase 0 schema."""

    _telemetry_validator().validate(payload)


class TelemetryGenerator:
    """Generate deterministic, schema-valid raw device telemetry."""

    def __init__(
        self,
        *,
        seed: int = 42,
        device_id: str = "biovolt-sim-01",
        cell_id: str = "cell-a",
        start_sequence: int = 1,
        start_od: float = 0.2,
        growth_rate_per_second: float = 0.001,
        bpw34_noise_amplitude: float = 12.0,
        voltage_noise_amplitude: float = 0.8,
        lux_noise_amplitude: float = 4.0,
        noise_amplitude: float | None = None,
    ) -> None:
        if not device_id.strip() or not cell_id.strip():
            raise ValueError("device_id and cell_id must not be blank")
        if start_sequence < 0:
            raise ValueError("start_sequence must be non-negative")
        if start_od < 0:
            raise ValueError("start_od must be non-negative")
        if growth_rate_per_second < 0:
            raise ValueError("growth_rate_per_second must be non-negative")
        amplitudes = (
            (noise_amplitude,) * 3
            if noise_amplitude is not None
            else (
                bpw34_noise_amplitude,
                voltage_noise_amplitude,
                lux_noise_amplitude,
            )
        )
        if any(amplitude < 0 for amplitude in amplitudes):
            raise ValueError("noise amplitudes must be non-negative")

        self.device_id = device_id
        self.cell_id = cell_id
        self.start_od = start_od
        self.growth_rate_per_second = growth_rate_per_second
        (
            self.bpw34_noise_amplitude,
            self.voltage_noise_amplitude,
            self.lux_noise_amplitude,
        ) = amplitudes
        self._random = random.Random(seed)
        self._next_sequence = start_sequence
        self._state = SimulatorState(sequence=start_sequence - 1, uptime_ms=0)

    @property
    def state(self) -> SimulatorState:
        """Return the state of the most recently emitted frame."""

        return self._state

    def next_frame(self, elapsed_seconds: float) -> dict[str, object]:
        """Return the next raw telemetry frame at the supplied elapsed time."""

        if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative")

        sequence = self._next_sequence
        uptime_ms = int(round(elapsed_seconds * 1000))
        if uptime_ms < self._state.uptime_ms:
            raise ValueError("elapsed_seconds must not regress simulator uptime")
        od_target = self.start_od + self.growth_rate_per_second * elapsed_seconds

        dark_raw = 320.0
        blank_raw = 23_840.0
        transmitted = dark_raw + (blank_raw - dark_raw) * 10 ** (-od_target)
        bpw34_raw = _bounded_int(
            round(transmitted + self._noise(self.bpw34_noise_amplitude)),
            minimum=-32768,
            maximum=32767,
        )

        voltage_mv = 438.2 + 3.0 * math.sin(elapsed_seconds / 30.0)
        voltage_mv += self._noise(self.voltage_noise_amplitude)
        voltage_mv = max(0.0, voltage_mv)
        bpv_adc_raw = _bounded_int(
            round(voltage_mv * 42.057), minimum=-32768, maximum=32767
        )

        grow_led_pwm = 130
        lux = 650.0 + grow_led_pwm * 2.0 + 20.0 * math.sin(elapsed_seconds / 45.0)
        lux = max(0.0, lux + self._noise(self.lux_noise_amplitude))

        frame: dict[str, Any] = {
            "schema_version": 1,
            "device_id": self.device_id,
            "sequence": sequence,
            "uptime_ms": uptime_ms,
            "cell_id": self.cell_id,
            "electrical": {
                "bpv_voltage_mv": round(voltage_mv, 3),
                "bpv_adc_raw": bpv_adc_raw,
            },
            "optical": {
                "bpw34_raw": bpw34_raw,
                "bpw34_voltage_mv": round(bpw34_raw * 3300.0 / 32767.0, 3),
                "led_680_enabled": True,
            },
            "environment": {
                "temperature_c": round(
                    26.0 + 0.3 * math.sin(elapsed_seconds / 60.0), 3
                ),
                "lux": round(lux, 3),
            },
            "actuators": {
                "grow_led_pwm": grow_led_pwm,
                "mixer_on": False,
            },
            "control": {
                "mode": "adaptive",
                "optimizer_direction": 0,
            },
            "health": {
                "ads1115_ok": True,
                "bpw34_ok": True,
                "temperature_ok": True,
                "light_sensor_ok": True,
            },
        }
        validate_telemetry_frame(frame)
        self._state = SimulatorState(sequence=sequence, uptime_ms=uptime_ms)
        self._next_sequence += 1
        return frame

    def _noise(self, amplitude: float) -> float:
        return self._random.uniform(-amplitude, amplitude) if amplitude else 0.0


def _bounded_int(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
