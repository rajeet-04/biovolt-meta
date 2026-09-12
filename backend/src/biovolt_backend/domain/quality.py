from pydantic import BaseModel


class DerivationQuality(BaseModel):
    electrical_eligible: bool
    od_eligible: bool
    biomass_eligible: bool
    carbon_eligible: bool
    biomass_extrapolated: bool
    reasons: list[str]


def compose_quality(
    *,
    electrical_eligible: bool,
    od_eligible: bool,
    biomass_eligible: bool,
    carbon_eligible: bool,
    biomass_extrapolated: bool = False,
    reasons: list[str] | None = None,
) -> DerivationQuality:
    return DerivationQuality(
        electrical_eligible=electrical_eligible,
        od_eligible=od_eligible,
        biomass_eligible=biomass_eligible,
        carbon_eligible=carbon_eligible,
        biomass_extrapolated=biomass_extrapolated,
        reasons=list(reasons or []),
    )
