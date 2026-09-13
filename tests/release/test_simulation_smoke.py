from scripts.release.phase9_simulation_gate import evaluate
from scripts.release.simulation_smoke import run


def test_simulated_soak_is_explicit_and_schema_valid() -> None:
    report = run(minutes=1)
    assert report["evidence_class"] == "synthetic_demo"
    assert report["hardware_hil"] is False
    assert report["frames"] == 121


def test_simulated_sensor_fault_preserves_explicit_null_health() -> None:
    report = run(minutes=1, fault="light_null")
    assert report["fault"] == "light_null"
    assert report["fault_frames"] == 121


def test_simulation_gate_passes_only_as_simulation_candidate() -> None:
    result = evaluate(run(minutes=60, fault="light_null"))
    assert result["status"] == "PASS"
    assert result["mode"] == "simulation"
    assert result["hardware_release"] is False


def test_simulation_gate_rejects_hardware_claims() -> None:
    result = evaluate({"evidence_class": "measured", "hardware_hil": True})
    assert result["status"] == "FAIL"
