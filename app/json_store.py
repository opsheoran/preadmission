import json
from pathlib import Path
from typing import Any


def _data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def _file_path(key: str) -> Path:
    safe = "".join(ch for ch in key if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid storage key")
    return _data_dir() / f"{safe}.json"


def load_records(key: str) -> list[dict[str, Any]]:
    path = _file_path(key)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
    except Exception:
        return []
    return []


def save_records(key: str, records: list[dict[str, Any]]) -> None:
    path = _file_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def next_id(records: list[dict[str, Any]]) -> int:
    max_id = 0
    for r in records:
        try:
            max_id = max(max_id, int(r.get("id") or 0))
        except Exception:
            continue
    return max_id + 1

