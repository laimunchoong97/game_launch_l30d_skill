#!/usr/bin/env python3
"""Collect public Steam facts for a game without credentials."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "game-sentiment-checker-l30d/0.1 (+public-data-research)"


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_appid(query: str, country: str, language: str) -> tuple[int | None, list[dict[str, Any]], str | None]:
    url = (
        "https://store.steampowered.com/api/storesearch/?term="
        f"{quote(query)}&l={quote(language)}&cc={quote(country)}"
    )
    try:
        payload = fetch_json(url)
    except Exception as exc:  # pragma: no cover - network failure is environment-specific
        return None, [], str(exc)

    items = payload.get("items") or []
    candidates = [
        {
            "appid": item.get("id"),
            "name": item.get("name"),
            "type": item.get("type"),
            "price": item.get("price"),
        }
        for item in items[:10]
    ]
    appid = candidates[0].get("appid") if candidates else None
    return appid, candidates, None


def normalize_appdetails(payload: dict[str, Any], appid: int) -> dict[str, Any]:
    entry = payload.get(str(appid)) or {}
    data = entry.get("data") or {}
    price = data.get("price_overview") or {}
    release = data.get("release_date") or {}
    platforms = data.get("platforms") or {}
    return {
        "appid": appid,
        "success": bool(entry.get("success")),
        "name": data.get("name"),
        "type": data.get("type"),
        "developer": data.get("developers") or [],
        "publisher": data.get("publishers") or [],
        "genres": [genre.get("description") for genre in data.get("genres") or []],
        "categories": [category.get("description") for category in data.get("categories") or []],
        "release_date": release.get("date"),
        "coming_soon": release.get("coming_soon"),
        "platforms": {name: bool(platforms.get(name)) for name in ("windows", "mac", "linux")},
        "is_free": data.get("is_free"),
        "price": {
            "currency": price.get("currency"),
            "initial": price.get("initial"),
            "final": price.get("final"),
            "discount_percent": price.get("discount_percent"),
            "initial_formatted": price.get("initial_formatted"),
            "final_formatted": price.get("final_formatted"),
        }
        if price
        else None,
        "metacritic": data.get("metacritic"),
        "recommendations": data.get("recommendations"),
        "short_description": data.get("short_description"),
        "website": data.get("website"),
    }


def normalize_reviews(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("query_summary") or {}
    return {
        "success": bool(payload.get("success")),
        "review_score": summary.get("review_score"),
        "review_score_desc": summary.get("review_score_desc"),
        "total_reviews": summary.get("total_reviews"),
        "total_positive": summary.get("total_positive"),
        "total_negative": summary.get("total_negative"),
        "positive_percent": (
            round(summary["total_positive"] / summary["total_reviews"] * 100, 2)
            if summary.get("total_reviews")
            else None
        ),
        "reviews": payload.get("reviews") or [],
    }


def collect(appid: int, country: str, language: str, review_count: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": "steam_public",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "appid": appid,
        "source_status": {},
    }

    details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={quote(country)}&l={quote(language)}"
    try:
        result["appdetails"] = normalize_appdetails(fetch_json(details_url), appid)
        result["source_status"]["appdetails"] = "ok"
    except Exception as exc:  # pragma: no cover - network failure is environment-specific
        result["appdetails"] = None
        result["source_status"]["appdetails"] = {"state": "error", "detail": str(exc)}

    reviews_url = (
        f"https://store.steampowered.com/appreviews/{appid}/?json=1&filter=recent"
        f"&language={quote(language)}&num_per_page={review_count}"
    )
    try:
        result["reviews"] = normalize_reviews(fetch_json(reviews_url))
        result["source_status"]["reviews"] = "ok"
    except Exception as exc:  # pragma: no cover - network failure is environment-specific
        result["reviews"] = None
        result["source_status"]["reviews"] = {"state": "error", "detail": str(exc)}

    players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    try:
        players = fetch_json(players_url)
        player_data = players.get("response") or {}
        result["current_players"] = {
            "success": player_data.get("result") == 1,
            "player_count": player_data.get("player_count"),
        }
        result["source_status"]["current_players"] = "ok"
    except Exception as exc:  # pragma: no cover - network failure is environment-specific
        result["current_players"] = None
        result["source_status"]["current_players"] = {"state": "error", "detail": str(exc)}

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--appid", type=int, help="Steam AppID")
    group.add_argument("--query", help="Game title to resolve through Steam store search")
    parser.add_argument("--country", default="us")
    parser.add_argument("--language", default="english")
    parser.add_argument("--reviews", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    candidates: list[dict[str, Any]] = []
    resolution_error = None
    appid = args.appid
    if args.query:
        appid, candidates, resolution_error = resolve_appid(args.query, args.country, args.language)
        if appid is None:
            payload = {
                "source": "steam_public",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source_status": {"store_search": "no-results" if not resolution_error else "error"},
                "query": args.query,
                "candidates": candidates,
                "error": resolution_error,
            }
        else:
            payload = collect(appid, args.country, args.language, args.reviews)
            payload["query"] = args.query
            payload["candidates"] = candidates
    else:
        payload = collect(appid, args.country, args.language, args.reviews)

    text = json.dumps(payload, ensure_ascii=True, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
