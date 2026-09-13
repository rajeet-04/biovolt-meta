from datetime import datetime

from pydantic import BaseModel, Field

from .state import ExperimentState


class AdaptiveConfig(BaseModel):
    initial_pwm: int = Field(default=64, ge=0, le=255)
    pwm_min: int = Field(default=0, ge=0, le=255)
    pwm_max: int = Field(default=255, ge=0, le=255)
    pwm_step: int = Field(default=4, ge=1, le=32)
    settle_ms: int = Field(default=3000, ge=500)
    minimum_valid_samples: int = Field(default=3, ge=1, le=9)
    objective_deadband_fraction: float = Field(default=0.01, ge=0, le=0.25)
    mixer_policy: str = Field(default="off", pattern="^(off|periodic)$")
    mixer_period_ms: int | None = Field(default=None, ge=1)
    mixer_on_ms: int | None = Field(default=None, ge=1)


class ExperimentArmInput(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    cell_id: str = Field(min_length=1, max_length=64)
    mode: str
    initial_led_pwm: int = Field(ge=0, le=255)
    initial_mixer_on: bool = False
    label: str | None = Field(default=None, max_length=128)
    calibration_revision_id: str | None = None
    adaptive: AdaptiveConfig | None = None


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    arms: list[ExperimentArmInput] = Field(default_factory=list)


class ExperimentDraftUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    arms: list[ExperimentArmInput] | None = None


class ExperimentArmView(ExperimentArmInput):
    id: str
    baseline_sequence: int | None = None
    baseline_timestamp: datetime | None = None
    baseline_biomass_g_l: float | None = None
    baseline_dry_biomass_g: float | None = None


class ExperimentView(BaseModel):
    id: str
    name: str
    state: ExperimentState
    description: str | None
    notes: str | None
    arms: list[ExperimentArmView]
