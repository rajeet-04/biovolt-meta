# Phase 0 Overview: Repository Foundation and Protocol Contracts

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze BioVolt repository boundaries, naming conventions, scientific data ownership, versioned JSON contracts, examples, validation, and CI before any firmware, backend, frontend, or deployment implementation begins.

**Architecture:** Phase 0 treats the repository as a contract-first monorepo. ESP32 raw measurements, FastAPI-derived scientific values, PWA visualization, commands, calibration, experiments, and system events are separated by explicit schemas so later phases can be developed independently without redefining payloads.

**Tech Stack:** Markdown, JSON Schema Draft 2020-12, Python 3.11+, `jsonschema`, `pytest`, GitHub Actions.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Phase 0 contains no FastAPI application implementation.
- Phase 0 contains no React application implementation.
- Phase 0 contains no ESP32 firmware implementation.
- Phase 0 contains no Docker, Nginx, or Cloudflared runtime implementation.
- JSON API fields use `snake_case`.
- Every protocol payload carries `schema_version: 1`.
- Raw telemetry contains only measured values, actuator state, control state, and health state.
- FastAPI later owns current, power, OD680, biomass, estimated CO2 biofixed into biomass, cumulative energy, and server timestamps.
- Missing sensor measurements use `null` plus an explicit health flag. They must never be replaced with misleading physical values such as `0`.
- ESP32 uses `sequence` and `uptime_ms`; FastAPI later supplies wall-clock timestamps.
- Current is derived from measured BPV voltage and a calibrated precision load resistor: `I = V / R`.
- Power is derived as `P = V^2 / R`.
- OD680 is derived from a 680 nm LED + BPW34 optical path using dark and blank references.
- Carbon wording is `estimated CO2 biofixed into biomass`; Phase 0 does not define this as direct room-air CO2 measurement.

---

## Phase 0 Module Map

### Module 0.1: Repository Structure and Conventions

Plan: `docs/superpowers/plans/phase_0/phase_0_1.md`

Produces:

- root repository skeleton
- root/component READMEs
- `.gitignore`
- `.editorconfig`
- repository layout test
- protocol naming and units documentation entry points

### Module 0.2: Raw Device Telemetry Contract

Plan: `docs/superpowers/plans/phase_0/phase_0_2.md`

Produces:

- `device-telemetry.v1.schema.json`
- canonical valid raw telemetry example
- raw telemetry schema tests
- explicit rules for sequence numbers, uptime, null handling, health flags, and measurement ownership

### Module 0.3: Processed Scientific Telemetry Contract

Plan: `docs/superpowers/plans/phase_0/phase_0_3.md`

Produces:

- `processed-telemetry.v1.schema.json`
- canonical processed telemetry example
- scientific derivation documentation
- schema tests for electrical and biological derived values

### Module 0.4: Commands, Calibration, Experiments, and Events

Plan: `docs/superpowers/plans/phase_0/phase_0_4.md`

Produces:

- device command schema
- calibration profile schema
- experiment schema
- system event schema
- canonical examples
- contract tests

### Module 0.5: Validation, CI, and Acceptance

Plan: `docs/superpowers/plans/phase_0/phase_0_5.md`

Produces:

- `scripts/validate_schemas.py`
- contract requirements
- full contract test suite
- GitHub Actions workflow
- final Phase 0 verification checklist

---

## Dependency Order

```text
0.1 Repository structure
        |
        v
0.2 Raw telemetry contract
        |
        v
0.3 Processed telemetry contract
        |
        v
0.4 Commands / calibration / experiments / events
        |
        v
0.5 Validation / CI / final acceptance
```

The modules are intentionally sequential because later contracts reuse naming, units, enums, and versioning decisions from earlier modules.

## Planned Repository State After Phase 0

```text
BioVolt/
├── backend/
│   └── README.md
├── firmware/
│   └── esp32/
│       └── README.md
├── frontend/
│   └── README.md
├── simulator/
│   └── README.md
├── shared/
│   ├── schemas/
│   │   ├── device-telemetry.v1.schema.json
│   │   ├── processed-telemetry.v1.schema.json
│   │   ├── device-command.v1.schema.json
│   │   ├── calibration-profile.v1.schema.json
│   │   ├── experiment.v1.schema.json
│   │   └── system-event.v1.schema.json
│   └── examples/
│       ├── device-telemetry.example.json
│       ├── processed-telemetry.example.json
│       ├── device-command.example.json
│       ├── calibration-profile.example.json
│       ├── experiment.example.json
│       └── system-event.example.json
├── docs/
│   ├── architecture/
│   │   └── software-architecture.md
│   ├── protocols/
│   │   ├── data-contract.md
│   │   └── versioning.md
│   └── superpowers/
│       └── plans/
│           └── phase_0/
│               ├── phase_0_0.md
│               ├── phase_0_1.md
│               ├── phase_0_2.md
│               ├── phase_0_3.md
│               ├── phase_0_4.md
│               └── phase_0_5.md
├── scripts/
│   └── validate_schemas.py
├── tests/
│   └── contracts/
│       ├── test_repository_layout.py
│       ├── test_device_telemetry_schema.py
│       ├── test_processed_telemetry_schema.py
│       ├── test_control_contracts.py
│       └── test_schema_examples.py
├── .github/
│   └── workflows/
│       └── contracts.yml
├── .editorconfig
├── .gitignore
├── requirements-contracts.txt
└── README.md
```

## Planned Commit Sequence

1. `chore: initialize BioVolt repository structure`
2. `docs: define BioVolt data ownership and units`
3. `feat: define raw BioVolt telemetry contract`
4. `feat: define processed scientific telemetry contract`
5. `feat: define control and experiment contracts`
6. `test: add contract validation and CI`

Each commit must leave the repository in a coherent state and must pass every test introduced up to that commit.

## Phase 0 Exit Criteria

- [ ] Repository boundaries are clear and documented.
- [ ] Raw device telemetry has a versioned schema and valid canonical example.
- [ ] Raw telemetry contains BPV voltage and optical receiver measurements, but not derived current, power, OD680, biomass, carbon, or cumulative energy.
- [ ] Processed telemetry has a separate versioned schema.
- [ ] Processed telemetry contains current, power, OD680, biomass, estimated CO2 biofixed into biomass, and cumulative energy.
- [ ] Load resistance lives in calibration/configuration, not as a repeatedly transmitted raw sensor value.
- [ ] Commands, calibration profiles, experiments, and events each have versioned contracts.
- [ ] Null and sensor-health behavior is documented and tested.
- [ ] Sequence and uptime behavior is documented and tested.
- [ ] Every canonical JSON example validates against its schema.
- [ ] At least one deliberately malformed example is rejected by each schema test module.
- [ ] `python scripts/validate_schemas.py` exits with status 0 for the repository state.
- [ ] `pytest tests/contracts -v` passes.
- [ ] GitHub Actions runs contract validation on pushes and pull requests.
- [ ] No application implementation has leaked into Phase 0.

## Handoff to Phase 1

Phase 1 may begin only after the Phase 0 contracts are merged. Phase 1 will consume these contracts to build the FastAPI backend and a fake ESP32 simulator without changing the meaning of Phase 0 fields. If a contract must change during Phase 1, the change must be reviewed as an explicit protocol revision rather than silently modifying payloads.
