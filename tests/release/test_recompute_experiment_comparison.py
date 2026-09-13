import json
import sys

from scripts.release.recompute_experiment_comparison import compare, main


def test_negative_gain_uses_the_common_window() -> None:
    result = compare(
        [(0, 10.0), (1000, 10.0), (2000, 10.0)],
        [(500, 5.0), (1500, 5.0), (2500, 5.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is True
    assert result["comparison_duration_s"] == 1.5
    assert result["passive_energy_mj"] == 0.015
    assert result["adaptive_energy_mj"] == 0.0075
    assert result["gain_pct"] == -50.0
    assert result["evidence_class"] == "measured"


def test_positive_gain_remains_eligible_and_positive() -> None:
    result = compare(
        [(0, 8.0), (1000, 8.0)],
        [(0, 10.0), (1000, 10.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is True
    assert result["gain_pct"] > 0


def test_nonpositive_denominator_is_ineligible_without_a_number() -> None:
    result = compare(
        [(0, 0.0), (1000, 0.0)],
        [(0, 1.0), (1000, 1.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert result["gain_pct"] is None
    assert "nonpositive_passive_energy" in result["reasons"]


def test_missing_overlap_is_ineligible() -> None:
    result = compare(
        [(0, 10.0), (1000, 10.0)],
        [(2000, 5.0), (3000, 5.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert result["comparison_duration_s"] is None
    assert "no_common_window" in result["reasons"]


def test_large_gap_is_ineligible_even_when_endpoints_exist() -> None:
    result = compare(
        [(0, 10.0), (1000, 10.0), (5000, 10.0)],
        [(0, 5.0), (1000, 5.0), (5000, 5.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert "telemetry_gap" in result["reasons"]


def test_gap_crossing_common_window_boundary_is_ineligible() -> None:
    result = compare(
        [(0, 10.0), (10_000, 10.0)],
        [(5_000, 5.0), (6_000, 5.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert "telemetry_gap" in result["reasons"]


def test_reboot_or_nonmonotonic_samples_are_ineligible() -> None:
    result = compare(
        [(0, 10.0), (1000, 10.0), (500, 10.0)],
        [(0, 5.0), (1000, 5.0)],
        passive_evidence="measured",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert "telemetry_reboot_or_nonmonotonic" in result["reasons"]


def test_synthetic_evidence_cannot_produce_a_measured_gain() -> None:
    result = compare(
        [(0, 10.0), (1000, 10.0)],
        [(0, 5.0), (1000, 5.0)],
        passive_evidence="synthetic_demo",
        adaptive_evidence="measured",
    )

    assert result["eligible"] is False
    assert result["gain_pct"] is None
    assert "evidence_class_not_measured" in result["reasons"]


def test_cli_emits_structured_recomputation(tmp_path, monkeypatch) -> None:
    source = tmp_path / "comparison.json"
    output = tmp_path / "analytics-recompute.json"
    source.write_text(
        json.dumps(
            {
                "passive": [[0, 10.0], [1000, 10.0]],
                "adaptive": [[0, 5.0], [1000, 5.0]],
                "passive_evidence": "measured",
                "adaptive_evidence": "measured",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["recompute_experiment_comparison", str(source), "--output", str(output)],
    )

    assert main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["eligible"] is True
