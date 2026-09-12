# BioVolt Data Contract

## Canonical Units

| Quantity | Field suffix | Unit |
|---|---|---|
| BPV voltage | `_mv` | millivolts |
| current | `_ua` | microamperes |
| power | `_uw` | microwatts |
| cumulative energy | `_mj` | millijoules |
| resistance | `_ohm` | ohms |
| temperature | `_c` | degrees Celsius |
| light | `lux` | lux |
| biomass concentration | `_g_l` | grams/litre |
| biomass mass | `_g` | grams |
| CO2 biofixed | `_g` | grams |
| device uptime | `_ms` | milliseconds |
| server timestamp | `timestamp` | ISO 8601 with timezone |

## Ownership

ESP32 owns raw measurements, actuator state, control state, sensor health, sequence, and uptime.
FastAPI owns server timestamps and scientific derived metrics.
React owns visualization only.

## Missing Measurements

A failed or unavailable physical sensor field is `null` and its corresponding health flag is `false`. Never substitute `0` for missing data.

## Raw vs Derived

Raw telemetry must not contain `current_ua`, `power_uw`, `od680`, biomass, CO2 biofixation, or cumulative energy.

## Electrical Derivations

Given `voltage_mv` and calibrated `load_resistance_ohm`:

`voltage_v = voltage_mv / 1000`

`current_ua = (voltage_v / load_resistance_ohm) * 1_000_000`

`power_uw = (voltage_v * voltage_v / load_resistance_ohm) * 1_000_000`

The load resistance is calibration/configuration data. It is not repeatedly transmitted by the ESP32.

## OD680 Derivation

Inputs:

- `I_sample`: corrected BPW34 sample reading with 680 nm LED active
- `I_dark`: BPW34 dark reference
- `I_blank`: BPW34 blank-medium reference

`ratio = (I_sample - I_dark) / (I_blank - I_dark)`

`od680 = -log10(ratio)`

OD680 must be `null` when:

- a required optical input is missing,
- `I_blank <= I_dark`,
- `I_sample <= I_dark`, or
- the ratio is not physically valid for the v1 calculation.

## Biomass and Carbon Estimate

Phase 0 defines a linear calibration model:

`biomass_g_l = slope * od680 + intercept`

`biomass_total_g = biomass_g_l * reactor_volume_l`

`biomass_delta_g = biomass_total_g - experiment_baseline_biomass_g`

`co2_biofixed_g = max(biomass_delta_g, 0) * 1.83`

This value is an estimated amount of CO2 biofixed into biomass. It is not direct gas-phase CO2 measurement and not a permanent sequestration claim.

Calibration values in canonical examples demonstrate contract structure only. They are not universal biological constants and must not be copied into experiments without calibration of the actual cell and reactor.
