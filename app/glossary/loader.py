from __future__ import annotations

from pathlib import Path
import re

import yaml


def load_metrics() -> dict:
    path = Path(__file__).with_name("metrics.yaml")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("metrics", {})


def match_metric_candidates(query: str) -> list[dict]:
    normalized = query.lower()
    words = set(re.findall(r"[a-z]+", normalized))
    ranking_words = {"best", "top", "worst", "biggest", "highest", "lowest", "least", "most", "strongest", "performing", "valuable", "recent"}
    for _, metric in load_metrics().items():
        aliases = [alias.lower() for alias in metric.get("aliases", [])]
        if any(alias in normalized for alias in aliases):
            return metric.get("candidates", [])
        if metric.get("aliases") and (
            ("employee" in words and words & ranking_words and any("employee" in alias for alias in aliases))
            or (words & {"customer", "customers", "client", "clients", "account", "accounts"} and words & ranking_words and any("customer" in alias for alias in aliases))
        ):
            return metric.get("candidates", [])
    return []


def candidates_for_entity(entity: str) -> list[dict]:
    metric_name = "employee_performance" if entity.lower() == "employee" else "customer_value"
    return load_metrics().get(metric_name, {}).get("candidates", [])
