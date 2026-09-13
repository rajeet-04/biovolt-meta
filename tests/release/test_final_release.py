from scripts.release.phase9_release_gate import evaluate_release
from scripts.release.recompute_experiment_comparison import compare


def test_comparison_keeps_negative_gain_and_requires_measured_evidence() -> None:
    passive = [(0, 10.0), (1000, 10.0)]
    adaptive = [(0, 8.0), (1000, 8.0)]
    result = compare(passive, adaptive, passive_evidence="measured", adaptive_evidence="measured")
    assert result["eligible"] is True
    assert result["gain_pct"] < 0


def test_comparison_returns_reason_for_synthetic_or_zero_denominator() -> None:
    result = compare(
        [(0, 0.0), (1000, 0.0)],
        [(0, 1.0), (1000, 1.0)],
        passive_evidence="synthetic",
        adaptive_evidence="measured",
    )
    assert result["eligible"] is False
    assert result["gain_pct"] is None
    assert result["reason"]


def test_final_gate_fails_closed_on_missing_required_reports() -> None:
    result = evaluate_release({"scientific": True})
    assert result["status"] == "FAIL"
    assert "resilience" in result["failed_gates"]
