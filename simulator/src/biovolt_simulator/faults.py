"""Pure, explicit fault transformations for simulator telemetry frames."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

SUPPORTED_FAULTS = frozenset(
    {"temperature_null", "light_null", "bpv_voltage_null", "bpw34_null"}
)


def apply_fault(payload: dict[str, object], fault: str) -> dict[str, object]:
    """Return a deep-copied payload with one explicit sensor fault applied."""

    if fault not in SUPPORTED_FAULTS:
        options = ", ".join(sorted(SUPPORTED_FAULTS))
        raise ValueError(f"unknown simulator fault {fault!r}; choose one of: {options}")

    result = deepcopy(payload)
    sections = cast(dict[str, dict[str, object]], result)
    health = sections["health"]

    if fault == "temperature_null":
        sections["environment"]["temperature_c"] = None
        health["temperature_ok"] = False
    elif fault == "light_null":
        sections["environment"]["lux"] = None
        health["light_sensor_ok"] = False
    elif fault == "bpv_voltage_null":
        sections["electrical"]["bpv_voltage_mv"] = None
        sections["electrical"]["bpv_adc_raw"] = None
        health["ads1115_ok"] = False
    else:  # fault == "bpw34_null"
        sections["optical"]["bpw34_raw"] = None
        sections["optical"]["bpw34_voltage_mv"] = None
        health["bpw34_ok"] = False

    return result
