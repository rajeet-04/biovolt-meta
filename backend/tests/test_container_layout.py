import json
from pathlib import Path

from biovolt_backend.contracts.loader import validate_payload


def test_backend_image_copies_contracts_to_loader_repository_root():
    repo = Path(__file__).resolve().parents[2]
    dockerfile = (repo / "backend/Dockerfile").read_text(encoding="utf-8")
    readme = (repo / "backend/README.md").read_text(encoding="utf-8")

    # ``pip install`` also places a copy in site-packages.  The source path
    # must win at runtime so repository_root() resolves /app, not the Python
    # installation prefix, in the container.
    assert "ENV PYTHONPATH=/app/backend/src" in dockerfile
    assert "COPY shared/schemas /app/shared/schemas" in dockerfile
    assert "COPY shared/examples /app/shared/examples" in dockerfile
    assert 'Path("/app/shared/examples/device-telemetry.example.json")' in readme
    assert "from biovolt_backend.contracts.loader import validate_payload" in readme
    assert 'validate_payload("device-telemetry.v1.schema.json", payload)' in readme

    payload = json.loads(
        (repo / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )
    validate_payload("device-telemetry.v1.schema.json", payload)
