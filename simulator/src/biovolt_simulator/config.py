"""Configuration for the BioVolt simulator."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulatorSettings(BaseSettings):
    """Runtime settings loaded from ``BIOVOLT_SIM_`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="BIOVOLT_SIM_",
        env_file=".env",
        extra="ignore",
    )

    backend_ws_url: str
    device_id: str = "biovolt-sim-01"
    cell_id: str = "cell-a"
    device_token: str
    interval_seconds: float = Field(default=0.5, gt=0)
    seed: int = 42
    start_sequence: int = Field(default=1, ge=0)

    @field_validator("device_token", "device_id", "cell_id")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value
