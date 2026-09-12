import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=None)
def load_schema(filename: str) -> dict[str, object]:
    path = repository_root() / "shared" / "schemas" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(filename: str, payload: dict[str, object]) -> None:
    Draft202012Validator(load_schema(filename)).validate(payload)
