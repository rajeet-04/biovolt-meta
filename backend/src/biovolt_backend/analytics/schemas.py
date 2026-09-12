from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    experiment_id: str
    evidence_class: str
    arm_count: int
    minimum_power_coverage_fraction: float = 0.8
    analytics_gap_threshold_s: float = 2.5
    comparison_method: str = "matched_elapsed_window"
    energy_method: str = "cumulative_difference_single_boot"


class EnergyComparisonView(BaseModel):
    eligible: bool
    passive_energy_mj: float | None
    adaptive_energy_mj: float | None
    gain_pct: float | None
    common_duration_s: float | None
    reasons: tuple[str, ...]
    passive_coverage_fraction: float | None = None
    adaptive_coverage_fraction: float | None = None
    passive_sample_count: int = 0
    adaptive_sample_count: int = 0


class AnalyticsSeriesPoint(BaseModel):
    elapsed_s: float
    passive_power_uw: float | None = None
    adaptive_power_uw: float | None = None
    passive_led_pwm: float | None = None
    adaptive_led_pwm: float | None = None
    passive_mixer_on: bool | None = None
    adaptive_mixer_on: bool | None = None


class AnalyticsSeriesView(BaseModel):
    experiment_id: str
    bucket_seconds: int
    points: tuple[AnalyticsSeriesPoint, ...]
