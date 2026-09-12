from dataclasses import dataclass
from datetime import datetime

from biovolt_backend.domain.quality import DerivationQuality


@dataclass(frozen=True)
class AnalyticsSample:
    received_at: datetime
    sequence: int
    uptime_ms: int
    power_uw: float | None
    cumulative_energy_mj: float | None
    od680: float | None
    biomass_g_l: float | None
    dry_biomass_g: float | None
    temperature_c: float | None
    grow_led_pwm: int
    mixer_on: bool
    quality: DerivationQuality


@dataclass(frozen=True)
class MatchedWindow:
    duration_s: float
    passive_samples: tuple[AnalyticsSample, ...]
    adaptive_samples: tuple[AnalyticsSample, ...]
