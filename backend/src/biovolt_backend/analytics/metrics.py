from dataclasses import dataclass
from statistics import mean, median

from .types import AnalyticsSample


@dataclass(frozen=True)
class ElectricalArmMetrics:
    mean_power_uw: float | None
    median_power_uw: float | None
    min_power_uw: float | None
    max_power_uw: float | None
    energy_mj: float | None
    energy_per_hour_mj_h: float | None


@dataclass(frozen=True)
class ControlArmMetrics:
    mean_grow_led_pwm: float | None
    led_pwm_change_count: int
    mixer_on_fraction: float | None


def electrical_metrics(
    samples: tuple[AnalyticsSample, ...], duration_s: float
) -> ElectricalArmMetrics:
    powers = [s.power_uw for s in samples if s.power_uw is not None]
    energies = [s.cumulative_energy_mj for s in samples]
    energy = None
    if (
        len(energies) >= 2
        and all(v is not None for v in energies)
        and all(b >= a for a, b in zip(energies, energies[1:], strict=False))
    ):
        energy = energies[-1] - energies[0]
    return ElectricalArmMetrics(
        mean(powers) if powers else None,
        median(powers) if powers else None,
        min(powers) if powers else None,
        max(powers) if powers else None,
        energy,
        energy / duration_s * 3600 if energy is not None and duration_s > 0 else None,
    )


def control_metrics(samples: tuple[AnalyticsSample, ...]) -> ControlArmMetrics:
    if not samples:
        return ControlArmMetrics(None, 0, None)
    return ControlArmMetrics(
        mean(s.grow_led_pwm for s in samples),
        sum(a.grow_led_pwm != b.grow_led_pwm for a, b in zip(samples, samples[1:], strict=False)),
        sum(s.mixer_on for s in samples) / len(samples),
    )
