import json
from pathlib import Path

from biovolt_backend.contracts.loader import validate_payload


def test_backend_image_copies_contracts_to_loader_repository_root():
    repo = Path(__file__).resolve().parents[2]
    dockerfile = (repo / "backend/Dockerfile").read_text(encoding="utf-8")
    assert "COPY shared/schemas /app/shared/schemas" in dockerfile
    assert "COPY shared/examples /app/shared/examples" in dockerfile

    payload = json.loads(
        (repo / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )
    validate_payload("device-telemetry.v1.schema.json", payload)
