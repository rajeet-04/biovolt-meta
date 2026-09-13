from scripts.release.validate_claim_traceability import build_report
from scripts.release.validate_production_analytics import build_report as analytics_report
from scripts.release.validate_release_security import scan


def test_analytics_report_uses_frozen_relative_energy_tolerance() -> None:
    independent = {
        "eligible": True,
        "passive_energy_mj": 10.0,
        "adaptive_energy_mj": 8.0,
        "gain_pct": -20.0,
        "comparison_duration_s": 60.0,
        "passive_coverage_fraction": 1.0,
        "adaptive_coverage_fraction": 1.0,
        "evidence_class": "measured",
    }
    production = {**independent, "passive_energy_mj": 10.009}

    report = analytics_report(independent, production)

    assert report["status"] == "PASS"


def test_analytics_report_fails_on_ineligible_reason_mismatch() -> None:
    independent = {"eligible": False, "reasons": ["telemetry_gap"]}
    production = {"eligible": False, "reasons": ["insufficient_passive_coverage"]}

    report = analytics_report(independent, production)

    assert report["status"] == "FAIL"
    assert report["findings"] == ["ineligible comparison reasons disagree"]


def test_analytics_report_requires_exact_evidence_class_for_ineligible_data() -> None:
    independent = {
        "eligible": False,
        "evidence_class": "synthetic_demo",
        "reasons": ["evidence_class_not_measured"],
    }
    production = {
        "eligible": False,
        "evidence_class": "measured",
        "reasons": ["evidence_class_not_measured"],
    }

    report = analytics_report(independent, production)

    assert report["status"] == "FAIL"
    assert report["findings"] == [
        "evidence_class disagrees between independent and production analytics"
    ]


def test_claim_report_requires_calibration_and_synthetic_label() -> None:
    claim = {
        "claim": "estimated biomass",
        "ui_field": "biomass_g_l",
        "api_field": "biomass_g_l",
        "experiment": "exp-1",
        "evidence_class": "synthetic_demo",
        "source": "export.csv",
        "requires_calibration": True,
    }

    report = build_report([claim])

    assert report["status"] == "FAIL"
    assert "calibration_revision" in report["findings"][0]
    assert "synthetic_demo" in report["findings"][1]


def test_security_scan_checks_values_not_documentation_words(tmp_path) -> None:
    safe = tmp_path / "safe.md"
    safe.write_text("Keep device tokens outside the evidence pack.", encoding="utf-8")
    unsafe = tmp_path / "report.json"
    unsafe.write_text('{"BIOVOLT_DEVICE_SHARED_TOKEN": "real-secret-value"}', encoding="utf-8")

    findings = scan(tmp_path)

    assert len(findings) == 1
    assert "report.json" in findings[0]
