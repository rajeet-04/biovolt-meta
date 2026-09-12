from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_compose_loads_dotenv_and_keeps_container_overrides_explicit() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "    env_file:\n      - .env\n" in compose
    assert "BIOVOLT_DATABASE_URL=sqlite+aiosqlite:////data/biovolt.db" in compose
    assert "BIOVOLT_DEVICE_SHARED_TOKEN=${BIOVOLT_DEVICE_SHARED_TOKEN:?" in compose
    assert "BIOVOLT_LOAD_RESISTANCE_OHM=${BIOVOLT_LOAD_RESISTANCE_OHM:-100000}" in compose
    assert (
        "BIOVOLT_BPW34_DARK_RAW"
        not in compose.split("    environment:", 1)[1].split("    volumes:", 1)[0]
    )
    assert (
        "BIOVOLT_BPW34_BLANK_RAW"
        not in compose.split("    environment:", 1)[1].split("    volumes:", 1)[0]
    )
