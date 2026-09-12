"""Validate actuator command safety evidence."""


def validate_events(events: list[dict[str, object]]) -> list[str]:
    findings: list[str] = []
    for index, event in enumerate(events, 1):
        if event.get("safe") is not True:
            findings.append(f"event {index}: actuator safety violation")
        if event.get("replayed") is not False:
            findings.append(f"event {index}: stale command replay")
        if event.get("clamped") is not True:
            findings.append(f"event {index}: out-of-range command was not clamped/rejected")
    return findings
