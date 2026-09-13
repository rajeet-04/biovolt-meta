"""Validate explicit sensor-failure semantics."""


def validate_faults(records: list[dict[str, object]]) -> list[str]:
    findings: list[str] = []
    for record in records:
        sensor = str(record.get("sensor", "unknown"))
        if record.get("value") is not None:
            findings.append(f"{sensor}: failed value was fabricated")
        if record.get("health") is not False:
            findings.append(f"{sensor}: health did not become false")
        if record.get("unrelated_continues") is not True:
            findings.append(f"{sensor}: unrelated acquisition did not continue")
        if record.get("rebooted") is not False:
            findings.append(f"{sensor}: routine fault rebooted the device")
    return findings
