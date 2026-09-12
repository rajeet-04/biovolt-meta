import json
from datetime import datetime
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def _is_rfc3339_datetime(value: object) -> bool:
    if not isinstance(value, str) or len(value) < 11 or value[10] not in "Tt":
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


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
