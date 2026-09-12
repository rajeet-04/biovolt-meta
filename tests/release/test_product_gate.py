from scripts.release.phase9_product_gate import evaluate


def test_product_gate_requires_all_audits_and_zero_severity_findings() -> None:
    evidence = {
        "blockers": [],
        "majors": [],
        "journeys": {"judge": True, "operator": True, "recovery": True},
        "responsive": True,
        "accessibility": True,
        "screenshots": True,
    }
    assert evaluate(evidence)["eligible"] is True


def test_product_gate_blocks_missing_journey_or_major() -> None:
    result = evaluate({"blockers": [], "majors": ["ambiguous command state"]})
    assert result["eligible"] is False
    assert any("MAJOR" in finding for finding in result["findings"])
