"""Fail closed when a judge-facing headline lacks provenance."""


def validate_claims(claims: list[dict[str, object]]) -> list[str]:
    required = ("claim", "ui_field", "api_field", "experiment", "evidence_class", "source")
    findings: list[str] = []
    for index, claim in enumerate(claims, 1):
        missing = [field for field in required if not claim.get(field)]
        if missing:
            findings.append(f"claim {index} missing trace fields: {', '.join(missing)}")
    return findings
