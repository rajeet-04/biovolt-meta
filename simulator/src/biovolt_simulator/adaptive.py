"""Deterministic synthetic Adaptive controller used only by simulator tests."""
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class AdaptiveConfig:
    initial_pwm: int = 64
    pwm_min: int = 0
    pwm_max: int = 255
    pwm_step: int = 4
    deadband: float = 0.01

    def validate(self) -> None:
        if not self.pwm_min < self.pwm_max or not self.pwm_min <= self.initial_pwm <= self.pwm_max:
            raise ValueError("invalid PWM bounds")
        if not 0 < self.pwm_step <= min(32, self.pwm_max - self.pwm_min):
            raise ValueError("invalid PWM step")
        if not 0 <= self.deadband <= 0.25:
            raise ValueError("invalid deadband")


class SyntheticAdaptive:
    """Small deterministic synthetic P&O model; output is never biological evidence."""

    def __init__(self, config: AdaptiveConfig = AdaptiveConfig()) -> None:
        config.validate()
        self.config = config
        self.pwm = config.initial_pwm
        self.direction = 1
        self._previous: float | None = None

    def update(self, voltages_mv: list[float]) -> tuple[int, int]:
        objective = median(voltages_mv) ** 2
        if self._previous is not None:
            change = (objective - self._previous) / max(abs(self._previous), 1e-6)
            if change < -self.config.deadband:
                self.direction *= -1
        self._previous = objective
        proposed = self.pwm + self.direction * self.config.pwm_step
        if proposed > self.config.pwm_max or proposed < self.config.pwm_min:
            self.direction *= -1
            proposed = self.pwm + self.direction * self.config.pwm_step
        self.pwm = max(self.config.pwm_min, min(self.config.pwm_max, proposed))
        return self.pwm, self.direction
