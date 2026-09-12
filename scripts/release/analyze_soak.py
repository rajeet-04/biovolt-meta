"""Analyze a JSON-compatible soak sample list against frozen thresholds."""


def analyze(samples: list[dict[str, object]], interruptions: list[str]) -> list[str]:
    findings: list[str] = []
    if (
        len(samples) < 2
        or float(samples[-1].get("wall_s", 0)) - float(samples[0].get("wall_s", 0)) < 3600
    ):
        findings.append("soak must cover at least 60 continuous minutes")
    if set(interruptions) != {"backend_restart", "hotspot", "browser_restart"}:
        findings.append("soak must record backend, hotspot, and browser interruptions")
    if (
        samples
        and float(samples[-1].get("free_heap_bytes", 0))
        < float(samples[0].get("free_heap_bytes", 0)) * 0.85
    ):
        findings.append("final free heap is below 85% of baseline")
    return findings
