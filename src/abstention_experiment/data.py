from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any


DAYS: tuple[str, ...] = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
)

PROTOCOL_LABELS = {
    6: "TCP",
    17: "UDP",
    1: "ICMP",
    0: "UNKNOWN",
}


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _protocol_label(value: Any) -> str:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return "UNKNOWN"
    return PROTOCOL_LABELS.get(numeric, "UNKNOWN")


def map_protocol(values: Any) -> Any:
    if hasattr(values, "map"):
        return values.map(_protocol_label)
    return [_protocol_label(value) for value in values]
