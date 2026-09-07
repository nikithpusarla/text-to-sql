from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def log_event(event: str, payload: dict[str, Any]) -> None:
    path = Path("logs")
    path.mkdir(exist_ok=True)
    with (path / "pipeline.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **payload}, default=str) + "\n")