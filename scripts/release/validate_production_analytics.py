"""Compare independent and production analytics with frozen tolerances."""


def validate(independent: dict[str, object], production: dict[str, object]) -> list[str]:
    findings: list[str] = []
    if independent.get("eligible") != production.get("eligible"):
        findings.append("eligibility disagrees between independent and production analytics")
    if independent.get("eligible"):
        for field, tolerance in (
            ("passive_energy_mj", 0.001),
            ("adaptive_energy_mj", 0.001),
            ("gain_pct", 0.05),
        ):
            if abs(float(independent.get(field, 0)) - float(production.get(field, 0))) > tolerance:
                findings.append(f"{field} exceeds its release tolerance")
    elif independent.get("reason") != production.get("reason"):
        findings.append("ineligible comparison reason disagrees")
    return findings
