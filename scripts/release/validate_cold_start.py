"""Validate repeatable, safe cold-start evidence without requiring Docker."""


def validate_runs(runs: list[dict[str, object]]) -> list[str]:
    findings: list[str] = []
    if len(runs) < 3:
        findings.append("three cold-start runs are required")
    for index, run in enumerate(runs, 1):
        if float(run.get("mandatory_healthy_s", 999)) > 90:
            findings.append(f"run {index}: mandatory services exceeded 90 seconds")
        if float(run.get("telemetry_recovery_s", 999)) > 30:
            findings.append(f"run {index}: telemetry recovery exceeded 30 seconds")
        if run.get("boot_actuator_safe") is not True:
            findings.append(f"run {index}: actuator boot state was unsafe")
        if run.get("fake_live") is not False:
            findings.append(f"run {index}: live state appeared without fresh telemetry")
    return findings
