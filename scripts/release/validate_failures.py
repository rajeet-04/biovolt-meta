"""Validate controlled service/network interruption evidence."""

RECOVERY_LIMITS = {"backend_restart": 30, "hotspot": 30, "nginx_restart": 15}


def validate_matrix(records: list[dict[str, object]]) -> list[str]:
    findings: list[str] = []
    for record in records:
        scenario = str(record.get("scenario", "unknown"))
        if record.get("safe") is not True:
            findings.append(f"{scenario}: local safety was not maintained")
        if record.get("replayed") is not False:
            findings.append(f"{scenario}: stale command replay detected")
        limit = RECOVERY_LIMITS.get(scenario)
        if limit is not None and float(record.get("recovery_s", 999)) > limit:
            findings.append(f"{scenario}: recovery exceeded {limit} seconds")
        if (
            scenario in {"backend_restart", "nginx_restart", "hotspot"}
            and record.get("state") == "live"
        ):
            findings.append(f"{scenario}: failure state was incorrectly shown as live")
    return findings
