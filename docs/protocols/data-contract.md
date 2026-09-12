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
