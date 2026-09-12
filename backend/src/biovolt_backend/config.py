from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BIOVOLT_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "BioVolt Backend"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///../data/biovolt.db"
    export_dir: str = "/data/exports"
    device_shared_token: str = Field(default="change-me", min_length=8)
    operator_pin_hash: str | None = Field(default=None, repr=False)
    load_resistance_ohm: float = Field(default=100_000.0, gt=0)
    bpw34_dark_raw: float | None = None
    bpw34_blank_raw: float | None = None
    evidence_class: Literal["measured", "synthetic_demo"] = "measured"

    @field_validator("bpw34_dark_raw", "bpw34_blank_raw", mode="before")
    @classmethod
    def blank_calibration_is_unset(cls, value: object) -> object:
        """Treat an explicitly blank optional calibration as an omitted value."""
        if isinstance(value, str) and not value.strip():
            return None
        return value
