#!/usr/bin/env python3
"""Render a normalized game sense-check JSON bundle as self-contained HTML."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def esc(value: Any) -> str:
    if value is None or value == "":
        return "Unavailable"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (dict, list)):
        return html.escape(json.dumps(value, ensure_ascii=True, sort_keys=True))
    return html.escape(str(value))


def safe_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return html.escape(value, quote=True)
    return None


def link(label: Any, url: Any) -> str:
    safe = safe_url(url)
    if not safe:
        return esc(label)
    return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def value_list(values: Any) -> str:
    if not values:
        return '<p class="muted">Unavailable</p>'
    if not isinstance(values, list):
        values = [values]
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in values) + "</ul>"


def key_value_grid(values: Any) -> str:
    if not isinstance(values, dict) or not values:
        return '<p class="muted">Unavailable</p>'
    cells = []
    for key, value in values.items():
        cells.append(f'<div class="kv"><span>{esc(key.replace("_", " ").title())}</span><strong>{esc(value)}</strong></div>')
    return '<div class="kv-grid">' + "".join(cells) + "</div>"


def score_card(label: str, value: Any, modifier: str = "") -> str:
    displayed = esc(value)
    numeric = ""
    try:
        number = float(value)
        numeric = "high" if number >= 80 else "mid" if number >= 50 else "low"
    except (TypeError, ValueError):
        numeric = "neutral"
    return f'<div class="score-card {numeric} {modifier}"><span>{esc(label)}</span><strong>{displayed}</strong></div>'


def rows(items: Any, columns: list[str]) -> str:
    if not isinstance(items, list) or not items:
        return '<tr><td colspan="%d" class="muted">Unavailable</td></tr>' % len(columns)
    output = []
    for item in items:
        if not isinstance(item, dict):
            item = {columns[0]: item}
        cells = []
        for column in columns:
            value = item.get(column)
            if column == "source" and isinstance(value, dict):
                cells.append(f"<td>{link(value.get('name'), value.get('url'))}</td>")
            else:
                cells.append(f"<td>{esc(value)}</td>")
        output.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(output)


def source_list(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return '<p class="muted">Unavailable</p>'
    output = []
    for item in items:
        if isinstance(item, dict):
            label = item.get("name") or item.get("source") or "Source"
            finding = item.get("finding") or item.get("detail") or ""
            date = item.get("captured_at") or item.get("date")
            suffix = f" <small>{esc(date)}</small>" if date else ""
            output.append(f"<li>{link(label, item.get('url'))}: {esc(finding)}{suffix}</li>")
        else:
            output.append(f"<li>{esc(item)}</li>")
    return "<ul>" + "".join(output) + "</ul>"


def section(title: str, body: str, anchor: str) -> str:
    return f'<section id="{esc(anchor)}"><h2>{esc(title)}</h2>{body}</section>'


def render_report(report: dict[str, Any]) -> str:
    snapshot = report.get("snapshot") or {}
    scores = report.get("scores") or {}
    recommendation = report.get("recommendation") or {}
    game = snapshot.get("game") or report.get("game") or "Game release sense-check"
    captured = snapshot.get("data_captured") or report.get("data_captured") or datetime.now(timezone.utc).isoformat()

    cards = "".join(
        [
            score_card("Demand potential", scores.get("demand_potential")),
            score_card("Purchase intent", scores.get("purchase_intent")),
            score_card("Launch momentum", scores.get("launch_momentum")),
            score_card("Reception health", scores.get("reception_health")),
            score_card("Market/markdown risk", scores.get("market_markdown_risk"), "risk"),
            score_card("Evidence confidence", scores.get("evidence_confidence", "Unavailable"), "confidence"),
        ]
    )

    snapshot_body = f"""
    <div class="hero-meta">{esc(snapshot.get('release_phase'))} <span>·</span> Captured {esc(captured)}</div>
    <div class="score-grid">{cards}</div>
    <div class="snapshot-grid">{key_value_grid({k: v for k, v in snapshot.items() if k not in {'game', 'data_captured', 'release_phase'}})}</div>
    """

    recommendation_body = f"""
    <div class="recommendation"><strong>{esc(recommendation.get('posture') or scores.get('overall_posture'))}</strong>
    <p>{esc(recommendation.get('summary'))}</p></div>
    <div class="two-col"><div><h3>Primary reason</h3><p>{esc(recommendation.get('primary_reason'))}</p></div>
    <div><h3>Main risk</h3><p>{esc(recommendation.get('main_risk'))}</p></div></div>
    <h3>What would change the recommendation</h3><p>{esc(recommendation.get('change_trigger'))}</p>
    """

    breakdown = report.get("score_breakdown") or []
    score_table = f'<div class="table-wrap"><table><thead><tr><th>Score</th><th>Result</th><th>Logic</th></tr></thead><tbody>{rows(breakdown, ["name", "score", "logic"])}</tbody></table></div>'

    evidence = report.get("demand_evidence") or {}
    demand_body = f"""
    <h3>Steam and SteamDB signals</h3>{key_value_grid(evidence.get('steamdb_signals') or evidence.get('steam_signals'))}
    <h3>Attention and audience signals</h3>{key_value_grid(evidence.get('attention_signals'))}
    <h3>Strongest demand signals</h3>{value_list(evidence.get('strongest_signals'))}
    <h3>Weakest or most uncertain signals</h3>{value_list(evidence.get('weakest_signals'))}
    """

    intent = report.get("purchase_intent") or {}
    intent_body = f"""
    {key_value_grid(intent.get('mix'))}
    <div class="callout"><strong>Hype-to-intent gap: {esc(intent.get('hype_to_intent_gap'))}</strong><p>{esc(intent.get('meaning'))}</p></div>
    """

    reception = report.get("reception") or report.get("sentiment") or {}
    aspects = reception.get("aspects") or []
    reception_body = f"""
    <div class="three-col">{key_value_grid({'Overall sentiment': reception.get('overall_sentiment'), 'Sentiment trend': reception.get('trend'), 'Sentiment confidence': reception.get('confidence')})}</div>
    <div class="table-wrap"><table><thead><tr><th>Aspect</th><th>Sentiment</th><th>Frequency</th><th>Purchase impact</th></tr></thead><tbody>{rows(aspects, ['aspect', 'sentiment', 'frequency', 'purchase_impact'])}</tbody></table></div>
    <h3>Important concerns</h3>{value_list(reception.get('important_concerns'))}
    """

    comparables = report.get("comparables") or {}
    comparable_body = f"""
    <p><strong>Selection criteria:</strong> {esc(comparables.get('selection_criteria'))}</p>
    <div class="table-wrap"><table><thead><tr><th>Comparable</th><th>Why comparable</th><th>Launch evidence</th><th>Outcome</th></tr></thead><tbody>{rows(comparables.get('items'), ['name', 'why_comparable', 'launch_evidence', 'outcome'])}</tbody></table></div>
    {key_value_grid(comparables.get('demand_range'))}
    <p><strong>Important caveat:</strong> {esc(comparables.get('caveat'))}</p>
    """

    price = report.get("price_risk") or {}
    price_body = key_value_grid(price.get("details") or price)

    sales = report.get("sales_player_evidence") or {}
    sales_body = f"""
    <h3>Confirmed public sales</h3>{source_list(sales.get('confirmed_sales'))}
    <h3>Third-party estimates</h3>{source_list(sales.get('estimates'))}
    <h3>Player evidence</h3>{key_value_grid(sales.get('player_evidence'))}
    """

    inventory = report.get("inventory") or {}
    inventory_body = f"""
    <div class="recommendation"><strong>{esc(inventory.get('posture'))}</strong><p>{esc(inventory.get('allocation'))}</p></div>
    <p><strong>Public-data basis:</strong> {esc(inventory.get('public_data_basis'))}</p>
    <h3>Assumptions</h3>{value_list(inventory.get('assumptions'))}
    """

    signals = report.get("reorder_stop") or {}
    signals_body = f"""
    <div class="two-col"><div><h3>Increase allocation if</h3>{value_list(signals.get('increase_if'))}</div>
    <div><h3>Reduce or stop buying if</h3>{value_list(signals.get('reduce_or_stop_if'))}</div></div>
    """

    coverage = report.get("coverage") or {}
    evidence_body = f"""
    <h3>Strong evidence</h3>{source_list(coverage.get('strong'))}
    <h3>Moderate evidence</h3>{source_list(coverage.get('moderate'))}
    <h3>Weak or proxy evidence</h3>{source_list(coverage.get('weak'))}
    <h3>Unavailable</h3>{value_list(coverage.get('unavailable'))}
    <h3>Source status</h3><div class="table-wrap"><table><thead><tr><th>Source</th><th>Status</th><th>Note</th></tr></thead><tbody>{rows(coverage.get('source_status'), ['source', 'status', 'note'])}</tbody></table></div>
    """

    sections = "".join(
        [
            section("1. Decision Snapshot", snapshot_body, "snapshot"),
            section("2. Executive Recommendation", recommendation_body, "recommendation"),
            section("3. Score Breakdown", score_table, "scores"),
            section("4. Demand Evidence", demand_body, "demand"),
            section("5. Purchase-Intent Analysis", intent_body, "intent"),
            section("6. Sentiment and Reception Analysis", reception_body, "reception"),
            section("7. Comparable Games", comparable_body, "comparables"),
            section("8. Price and Markdown Risk", price_body, "price-risk"),
            section("9. Public Sales and Player Evidence", sales_body, "sales"),
            section("10. Inventory Recommendation", inventory_body, "inventory"),
            section("11. Reorder and Stop Signals", signals_body, "signals"),
            section("12. Evidence and Coverage", evidence_body, "coverage"),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(game)} - Game Release Sense-Check</title>
<style>
:root {{ --ink:#16212b; --muted:#687581; --line:#dbe3e8; --paper:#f5f7f6; --card:#fff; --accent:#0f766e; --accent-soft:#d9f2ed; --warn:#b45309; --warn-soft:#fff0d5; --shadow:0 14px 40px rgba(22,33,43,.08); }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:linear-gradient(135deg,#eef5f2,#f9f5ed 55%,#edf2f7); color:var(--ink); font:15px/1.65 Georgia,serif; }}
.page {{ max-width:1120px; margin:0 auto; padding:32px 20px 64px; }}
header {{ background:linear-gradient(135deg,#102a2a,#175f5d); color:#fff; padding:42px; border-radius:24px; box-shadow:var(--shadow); margin-bottom:24px; }}
header h1 {{ font:700 clamp(28px,5vw,52px)/1.05 Georgia,serif; margin:0 0 12px; letter-spacing:-.03em; }} header p {{ margin:0; color:#d8efea; }}
section {{ background:rgba(255,255,255,.9); border:1px solid rgba(219,227,232,.9); border-radius:18px; padding:26px; margin:18px 0; box-shadow:0 8px 28px rgba(22,33,43,.05); }}
h2 {{ font:700 25px/1.2 Georgia,serif; margin:0 0 20px; }} h3 {{ font:700 17px/1.25 Georgia,serif; margin:22px 0 8px; }} p {{ margin:8px 0 14px; }} .muted, small {{ color:var(--muted); }}
.hero-meta {{ color:#d8efea; margin-bottom:22px; }} .hero-meta span {{ padding:0 7px; opacity:.6; }} .score-grid {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; }}
.score-card {{ background:#f2fbf8; border:1px solid #cbe8e0; border-radius:13px; padding:14px; min-height:105px; display:flex; flex-direction:column; justify-content:space-between; }} .score-card span {{ font:12px/1.3 Arial,sans-serif; color:#4f6c68; }} .score-card strong {{ font:700 26px/1 Arial,sans-serif; }} .score-card.low {{ background:#fff5ed; border-color:#f5ceb0; }} .score-card.risk {{ background:var(--warn-soft); border-color:#f1d39b; }} .score-card.confidence {{ background:#eef2ff; border-color:#d6ddff; }}
.snapshot-grid {{ margin-top:18px; }} .kv-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; }} .kv {{ border:1px solid var(--line); border-radius:10px; padding:11px 13px; background:#fbfcfc; }} .kv span {{ display:block; text-transform:capitalize; color:var(--muted); font:11px Arial,sans-serif; margin-bottom:4px; }} .kv strong {{ font:600 14px/1.35 Arial,sans-serif; }}
.recommendation,.callout {{ border-left:5px solid var(--accent); background:var(--accent-soft); padding:16px 18px; border-radius:0 12px 12px 0; }} .recommendation strong,.callout strong {{ font:700 20px/1.2 Arial,sans-serif; }}
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }} .three-col .kv-grid {{ grid-template-columns:repeat(3,1fr); }} .table-wrap {{ overflow-x:auto; }} table {{ width:100%; border-collapse:collapse; font:14px/1.45 Arial,sans-serif; }} th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:11px 9px; vertical-align:top; }} th {{ color:#53636d; font-size:12px; text-transform:uppercase; letter-spacing:.05em; }} ul {{ padding-left:22px; }} a {{ color:#0f766e; text-underline-offset:3px; }} footer {{ color:var(--muted); text-align:center; font:12px Arial,sans-serif; padding:20px; }}
@media (max-width:800px) {{ .score-grid {{ grid-template-columns:repeat(3,1fr); }} header {{ padding:30px 24px; }} }} @media (max-width:560px) {{ .page {{ padding:16px 10px 40px; }} section {{ padding:20px 16px; }} .score-grid {{ grid-template-columns:repeat(2,1fr); }} .two-col,.three-col .kv-grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main class="page">
<header><h1>{esc(game)}</h1><p>Game Release Sense-Check · Public-data market assessment · One game per report</p></header>
{sections}
<footer>Generated by Game sentiment checker l30d · Data captured {esc(captured)} · Public evidence only</footer>
</main></body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Normalized report JSON")
    parser.add_argument("--output", type=Path, required=True, help="HTML output path")
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(report), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
