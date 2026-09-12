from pydantic import BaseModel, Field


class BiomassPointInput(BaseModel):
    od680: float
    dry_biomass_g_l: float = Field(ge=0)


class CalibrationRevisionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    load_resistance_ohm: float
    ads1115_offset_mv: float
    optical_dark_raw: float | None = None
    optical_blank_raw: float | None = None
    biomass_points: list[BiomassPointInput] = []
    reactor_volume_l: float | None = None
    co2_per_dry_biomass_g_per_g: float | None = None
    source_notes: str | None = None


class CalibrationRevisionView(BaseModel):
    id: str
    profile_id: str
    revision_number: int
    validation: dict[str, str]
    biomass_slope: float | None = None
    biomass_intercept: float | None = None
    biomass_r_squared: float | None = None
    biomass_rmse_g_l: float | None = None
    biomass_point_count: int | None = None


class CalibrationProfileView(BaseModel):
    id: str
    name: str
    description: str | None
    active_revision_id: str | None
    revisions: list[CalibrationRevisionView]
