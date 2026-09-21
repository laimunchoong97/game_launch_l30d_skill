#!/usr/bin/env python3
"""Calculate reproducible scores from a normalized signal bundle.

Input format:
{
  "phase": "prelaunch",
  "signals": {
    "audience_intent": 4,
    "momentum": 3,
    "developer_franchise": 4,
    "comparables": 3,
    "creator_community": 4,
    "price_fit": 3,
    "competition": 2,
    "reception": 4,
    "player_engagement": 3,
    "public_sales": 2,
    "markdown_risk": 3
  }
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRELAUNCH_WEIGHTS = {
    "audience_intent": 20,
    "momentum": 20,
    "developer_franchise": 15,
    "comparables": 20,
    "creator_community": 10,
    "price_fit": 10,
    "competition": 5,
}

POSTLAUNCH_WEIGHTS = {
    "reception": 20,
    "player_engagement": 15,
    "public_sales": 20,
    "momentum": 15,
    "community_sentiment": 10,
    "markdown_risk": 10,
    "competition": 10,
}


def weighted_score(signals: dict[str, Any], weights: dict[str, int]) -> dict[str, Any]:
    available = {
        key: float(value)
        for key, value in signals.items()
        if key in weights and value is not None
    }
    if not available:
        return {"score": None, "coverage": 0, "available": [], "missing": list(weights)}

    used_weight = sum(weights[key] for key in available)
    raw = sum(
        (max(0.0, min(5.0, value)) / 5.0) * weights[key]
        for key, value in available.items()
    )
    score = round(raw / used_weight * 100, 1)
    return {
        "score": score,
        "coverage": round(used_weight / sum(weights.values()) * 100, 1),
        "available": sorted(available),
        "missing": sorted(set(weights) - set(available)),
    }


def confidence(coverage: float, source_count: int, agreement: str | None) -> str:
    if coverage >= 80 and source_count >= 4 and agreement == "high":
        return "High"
    if coverage >= 50 and source_count >= 2:
        return "Medium"
    return "Low"


def score(payload: dict[str, Any]) -> dict[str, Any]:
    phase = str(payload.get("phase", "prelaunch")).lower()
    weights = POSTLAUNCH_WEIGHTS if phase in {"launch", "postlaunch", "post-launch"} else PRELAUNCH_WEIGHTS
    signals = payload.get("signals") or {}
    main = weighted_score(signals, weights)
    risk = weighted_score(
        signals,
        {"markdown_risk": 40, "competition": 25, "technical_risk": 20, "evidence_uncertainty": 15},
    )
    source_count = int(payload.get("source_count", 0))
    agreement = payload.get("source_agreement")
    return {
        "phase": phase,
        "demand_or_reception_score": main,
        "market_risk_score": risk,
        "evidence_confidence": confidence(main["coverage"], source_count, agreement),
        "source_count": source_count,
        "source_agreement": agreement,
        "notes": [
            "Scores are relative signals, not reseller sales forecasts.",
            "Missing fields reduce coverage and confidence; they are not treated as zero demand.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    text = json.dumps(score(payload), ensure_ascii=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
