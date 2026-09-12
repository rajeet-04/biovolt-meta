from pydantic import Field
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
    device_shared_token: str = Field(default="change-me", min_length=8)
    load_resistance_ohm: float = Field(default=100_000.0, gt=0)
    bpw34_dark_raw: float | None = None
    bpw34_blank_raw: float | None = None
