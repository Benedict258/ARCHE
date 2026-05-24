from __future__ import annotations

import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


LAST_RECOMMENDATION_PATH = Path("data/last_recommend.json")
_LAST_RECOMMENDATION_CACHE: dict[str, Any] | None = None


def save_last_recommendation(payload: dict[str, Any], path: Path = LAST_RECOMMENDATION_PATH) -> None:
    """Persist the latest recommendation payload for explainability.

    Windows can briefly deny writes to the JSON file when tests or file indexers
    touch it. Keep an in-memory copy first, then retry an atomic disk write.
    """
    global _LAST_RECOMMENDATION_CACHE
    _LAST_RECOMMENDATION_CACHE = payload

    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, default=str)
    last_error: OSError | None = None

    for _ in range(3):
        tmp_path: str | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
            ) as handle:
                tmp_path = handle.name
                handle.write(data)
            os.replace(tmp_path, path)
            return
        except OSError as exc:
            last_error = exc
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except OSError:
                    pass
            time.sleep(0.05)

    try:
        path.write_text(data, encoding="utf-8")
    except OSError:
        if last_error:
            return


def load_last_recommendation(path: Path = LAST_RECOMMENDATION_PATH) -> dict[str, Any] | None:
    """Load the latest recommendation payload from disk or memory fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _LAST_RECOMMENDATION_CACHE
