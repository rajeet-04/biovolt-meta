import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from rfc3339_validator import validate_rfc3339


def _is_rfc3339_datetime(value: object) -> bool:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or len(value) < 11
        or value[10] not in "Tt"
    ):
        return False
    normalized = value[:10] + "T" + value[11:]
    if normalized.endswith("z"):
        normalized = normalized[:-1] + "Z"
    return bool(validate_rfc3339(normalized))


_FORMAT_CHECKER = FormatChecker()
_FORMAT_CHECKER.checks("date-time")(_is_rfc3339_datetime)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


@cache
def load_schema(filename: str) -> dict[str, object]:
    path = repository_root() / "shared" / "schemas" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(filename: str, payload: dict[str, object]) -> None:
    Draft202012Validator(load_schema(filename), format_checker=_FORMAT_CHECKER).validate(payload)
