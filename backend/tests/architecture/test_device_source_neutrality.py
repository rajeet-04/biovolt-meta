import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT / "backend" / "src"
BACKEND_PYPROJECT = ROOT / "backend" / "pyproject.toml"


def _backend_source() -> list[tuple[Path, str]]:
    return [(path, path.read_text(encoding="utf-8")) for path in BACKEND_SRC.rglob("*.py")]


def test_backend_does_not_import_simulator_package_or_depend_on_it() -> None:
    import_markers = ("biovolt_simulator", "from simulator", "import simulator")
    import_offenders = [
        str(path.relative_to(ROOT))
        for path, text in _backend_source()
        if any(marker in text for marker in import_markers)
    ]
    assert import_offenders == []

    project = tomllib.loads(BACKEND_PYPROJECT.read_text(encoding="utf-8"))["project"]
    dependencies = list(project.get("dependencies", []))
    for extras in project.get("optional-dependencies", {}).values():
        dependencies.extend(extras)
    dependency_names = {
        re.split(r"[<>=!~\[\s]", dependency, maxsplit=1)[0].lower() for dependency in dependencies
    }
    assert "biovolt-simulator" not in dependency_names


def test_backend_source_contains_no_simulator_specific_device_id() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path, text in _backend_source()
        if "biovolt-sim-" in text.lower()
    ]
    assert offenders == []
