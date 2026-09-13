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
