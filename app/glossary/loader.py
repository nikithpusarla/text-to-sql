from __future__ import annotations

from pathlib import Path

import yaml


def load_metrics() -> dict:
    path = Path(__file__).with_name("metrics.yaml")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("metrics", {})


def match_metric_candidates(query: str) -> list[dict]:
    normalized = query.lower()
    for _, metric in load_metrics().items():
        aliases = [alias.lower() for alias in metric.get("aliases", [])]
        if any(alias in normalized for alias in aliases):
            return metric.get("candidates", [])
    return []
