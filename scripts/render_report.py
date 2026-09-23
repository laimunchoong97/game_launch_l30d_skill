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


def badge(value: Any, kind: str = "neutral") -> str:
    return f'<span class="badge {esc(kind)}">{esc(value)}</span>'


def numeric_value(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(100.0, number))


def score_label(value: Any, risk: bool = False) -> str:
    number = numeric_value(value)
    if number is None:
        return "Unavailable"
    if risk:
        return "Low" if number < 35 else "Manageable" if number < 50 else "Elevated" if number < 65 else "High" if number < 80 else "Severe"
    return "Weak" if number < 35 else "Fragile" if number < 50 else "Uncertain" if number < 65 else "Promising" if number < 80 else "Strong"


def score_card(label: str, value: Any, modifier: str = "", risk: bool = False) -> str:
    number = numeric_value(value)
    if number is None:
        return f'<div class="metric {esc(modifier)}"><div class="metric-top"><span>{esc(label)}</span><strong>{esc(value)}</strong></div><div class="metric-track"><i class="unknown"></i></div><small>Coverage unavailable</small></div>'
    status = "low" if number < 50 else "mid" if number < 80 else "high"
    label_text = score_label(number, risk)
    return f'<div class="metric {esc(modifier)} {status}"><div class="metric-top"><span>{esc(label)}</span><strong>{int(number) if number.is_integer() else number}</strong></div><div class="metric-track"><i style="width:{number:.1f}%"></i></div><small>{esc(label_text)}{" - higher is worse" if risk else ""}</small></div>'


def value_list(values: Any, ordered: bool = False) -> str:
    if not values:
        return '<p class="muted">Unavailable</p>'
    if not isinstance(values, list):
        values = [values]
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{esc(item)}</li>" for item in values) + f"</{tag}>"


def key_value_grid(values: Any, compact: bool = False) -> str:
    if not isinstance(values, dict) or not values:
        return '<p class="muted">Unavailable</p>'
    cells = []
    for key, value in values.items():
        cells.append(f'<div class="fact"><span>{esc(str(key).replace("_", " ").title())}</span><strong>{esc(value)}</strong></div>')
    class_name = "fact-grid compact" if compact else "fact-grid"
    return f'<div class="{class_name}">' + "".join(cells) + "</div>"


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


def table(items: Any, columns: list[tuple[str, str]]) -> str:
    keys = [key for key, _ in columns]
    heads = "".join(f"<th>{esc(label)}</th>" for _, label in columns)
    return f'<div class="table-wrap"><table><thead><tr>{heads}</tr></thead><tbody>{rows(items, keys)}</tbody></table></div>'


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
    return '<ul class="source-list">' + "".join(output) + "</ul>"


def community_quotes(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return '<p class="muted">No usable item-level community quotes were collected.</p>'
    output = []
    for item in items:
        if not isinstance(item, dict):
            output.append(f"<li>{esc(item)}</li>")
            continue
        source = link(item.get("source") or "Community source", item.get("url"))
        author = esc(item.get("author") or item.get("commenter") or "Anonymous")
        engagement = esc(item.get("engagement") or item.get("upvotes") or "Unavailable")
        quote = esc(item.get("quote") or item.get("text"))
        output.append(f'<article class="quote-card"><div class="quote-meta"><strong>{source}</strong><span>{author}</span><span>{engagement}</span></div><q>{quote}</q></article>')
    return '<div class="quote-grid">' + "".join(output) + "</div>"


def section(title: str, kicker: str, body: str, anchor: str, extra: str = "") -> str:
    return f'<section id="{esc(anchor)}" class="report-section {esc(extra)}"><div class="section-heading"><span>{esc(kicker)}</span><h2>{esc(title)}</h2></div>{body}</section>'


def render_report(report: dict[str, Any]) -> str:
    snapshot = report.get("snapshot") or {}
    scores = report.get("scores") or {}
    recommendation = report.get("recommendation") or {}
    game = snapshot.get("game") or report.get("game") or "Game release sense-check"
    captured = snapshot.get("data_captured") or report.get("data_captured") or datetime.now(timezone.utc).isoformat()
    phase = snapshot.get("release_phase") or "Release phase unavailable"
    community = report.get("community_voice") or {}
    evidence = report.get("demand_evidence") or {}

    score_cards = "".join(
        [
            score_card("Demand potential", scores.get("demand_potential")),
            score_card("Purchase intent", scores.get("purchase_intent")),
            score_card("Launch momentum", scores.get("launch_momentum")),
            score_card("Reception health", scores.get("reception_health")),
            score_card("Market / markdown risk", scores.get("market_markdown_risk"), "risk", risk=True),
            score_card("Evidence confidence", scores.get("evidence_confidence", "Unavailable"), "confidence"),
        ]
    )

    snapshot_facts = {k: v for k, v in snapshot.items() if k not in {"game", "data_captured", "release_phase"}}
    decision_body = f"""
    <div class="decision-layout">
      <div class="decision-main">
        <div class="decision-label">Recommended posture</div>
        <h2>{esc(recommendation.get('posture') or scores.get('overall_posture'))}</h2>
        <p>{esc(recommendation.get('summary'))}</p>
      </div>
      <div class="decision-reason"><span>Why this matters</span><strong>{esc(recommendation.get('primary_reason'))}</strong><em>Main risk: {esc(recommendation.get('main_risk'))}</em></div>
    </div>
    <div class="trigger-strip"><span>Recheck trigger</span><strong>{esc(recommendation.get('change_trigger'))}</strong></div>
    """

    signal_body = f"""
    <div class="signal-grid">
      <div class="signal-panel positive"><div class="panel-label">Supports demand</div>{value_list(evidence.get('strongest_signals'))}</div>
      <div class="signal-panel caution"><div class="panel-label">Reasons to stay controlled</div>{value_list(evidence.get('weakest_signals'))}</div>
    </div>
    """

    community_summary = f"""
    <div class="community-header">
      <div><div class="panel-label">Community pulse</div><h2>{esc(community.get('sentiment'))}</h2><p>{esc(community.get('status'))}</p></div>
      <div class="community-facts">{key_value_grid({'Launch-buy intent': community.get('launch_buy_intent'), 'Hype-to-intent gap': (report.get('purchase_intent') or {}).get('hype_to_intent_gap'), 'Evidence window': snapshot.get('research_window')}, compact=True)}</div>
    </div>
    <div class="community-reading"><div><span>Players are excited about</span><p>{esc(community.get('excited_about'))}</p></div><div><span>Players are objecting to</span><p>{esc(community.get('object_to'))}</p></div></div>
    {community_quotes(community.get('quotes'))}
    """

    breakdown = report.get("score_breakdown") or []
    score_table = table(breakdown, [("name", "Score"), ("score", "Result"), ("logic", "What the evidence means")])

    demand_body = f"""
    <div class="subsection"><div class="panel-label">Steam and SteamDB</div>{key_value_grid(evidence.get('steamdb_signals') or evidence.get('steam_signals'))}</div>
    <div class="subsection"><div class="panel-label">Attention and audience</div>{key_value_grid(evidence.get('attention_signals'))}</div>
    """

    intent = report.get("purchase_intent") or {}
    intent_body = f"""
    {key_value_grid(intent.get('mix'))}
    <div class="intent-callout"><div class="panel-label">Hype-to-intent gap: {esc(intent.get('hype_to_intent_gap'))}</div><p>{esc(intent.get('meaning'))}</p></div>
    """

    reception = report.get("reception") or report.get("sentiment") or {}
    aspects = reception.get("aspects") or []
    reception_body = f"""
    <div class="reception-split"><div class="reception-card critic"><div class="panel-label">Professional reception</div><p>{esc(reception.get('overall_sentiment'))}</p><strong>{esc(reception.get('confidence'))}</strong></div><div class="reception-card community"><div class="panel-label">Player / community reception</div><p>{esc(community.get('sentiment'))}</p><strong>{esc(community.get('status'))}</strong></div></div>
    <div class="subsection"><div class="panel-label">Aspect-level read</div>{table(aspects, [("aspect", "Aspect"), ("sentiment", "Sentiment"), ("frequency", "Frequency"), ("purchase_impact", "Purchase impact")])}</div>
    <h3>Important concerns</h3>{value_list(reception.get('important_concerns'))}
    """

    comparables = report.get("comparables") or {}
    comparable_body = f"""
    <p><strong>Selection criteria:</strong> {esc(comparables.get('selection_criteria'))}</p>
    {table(comparables.get('items'), [("name", "Comparable"), ("why_comparable", "Why it matches"), ("launch_evidence", "Public evidence"), ("outcome", "Read-through")])}
    <div class="range-grid">{key_value_grid(comparables.get('demand_range'))}</div>
    <p class="caveat"><strong>Important caveat:</strong> {esc(comparables.get('caveat'))}</p>
    """

    price = report.get("price_risk") or {}
    price_body = key_value_grid(price.get("details") or price)

    sales = report.get("sales_player_evidence") or {}
    sales_body = f"""
    <div class="two-col"><div><div class="panel-label">Confirmed public sales</div>{source_list(sales.get('confirmed_sales'))}</div><div><div class="panel-label">Third-party estimates</div>{source_list(sales.get('estimates'))}</div></div>
    <div class="subsection"><div class="panel-label">Player evidence</div>{key_value_grid(sales.get('player_evidence'))}</div>
    """

    inventory = report.get("inventory") or {}
    inventory_body = f"""
    <div class="action-card"><div class="action-title">{esc(inventory.get('posture'))}</div><p>{esc(inventory.get('allocation'))}</p></div>
    <div class="subsection"><div class="panel-label">Public-data basis</div><p>{esc(inventory.get('public_data_basis'))}</p></div>
    <div class="subsection"><div class="panel-label">Assumptions</div>{value_list(inventory.get('assumptions'))}</div>
    """

    signals = report.get("reorder_stop") or {}
    signals_body = f"""
    <div class="two-col"><div class="signal-panel positive"><div class="panel-label">Increase allocation if</div>{value_list(signals.get('increase_if'))}</div><div class="signal-panel caution"><div class="panel-label">Reduce or stop buying if</div>{value_list(signals.get('reduce_or_stop_if'))}</div></div>
    """

    coverage = report.get("coverage") or {}
    evidence_body = f"""
    <div class="two-col"><div><div class="panel-label">Strong evidence</div>{source_list(coverage.get('strong'))}</div><div><div class="panel-label">Moderate evidence</div>{source_list(coverage.get('moderate'))}</div></div>
    <div class="two-col"><div><div class="panel-label">Weak or proxy evidence</div>{source_list(coverage.get('weak'))}</div><div><div class="panel-label">Unavailable</div>{value_list(coverage.get('unavailable'))}</div></div>
    {table(coverage.get('source_status'), [("source", "Source"), ("status", "Status"), ("note", "Coverage note")])}
    """

    sections = "".join(
        [
            section("The decision", "01 / Decision", decision_body, "decision", "decision-section"),
            section("What is driving the call", "02 / Signals", signal_body, "signals", "signal-section"),
            section("Community pulse", "03 / What players are saying", community_summary, "community", "community-section"),
            section("Score dashboard", "04 / Scoring", f'<div class="score-table">{score_table}</div>', "scores"),
            section("Demand evidence", "05 / Demand", demand_body, "demand"),
            section("Purchase intent", "06 / Conversion", intent_body, "intent"),
            section("Reception analysis", "07 / Reception", reception_body, "reception"),
            section("Comparable releases", "08 / Benchmarks", comparable_body, "comparables"),
            section("Price and markdown risk", "09 / Risk", price_body, "price-risk"),
            section("Public sales and player evidence", "10 / Market evidence", sales_body, "sales"),
            section("Inventory action plan", "11 / Action", inventory_body, "inventory", "action-section"),
            section("Reorder and stop signals", "12 / Monitoring", signals_body, "monitoring"),
            section("Evidence coverage", "13 / Appendix", evidence_body, "coverage", "appendix-section"),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(game)} - Game Release Sense-Check</title>
<style>
:root {{ --ink:#1b2928; --muted:#667674; --line:#dbe5e0; --paper:#f5f1e8; --card:#fffdf8; --teal:#0f6b61; --teal-dark:#123b38; --teal-soft:#e1f1ec; --orange:#c76635; --orange-soft:#fff0e4; --blue:#426a82; --blue-soft:#eaf2f7; --shadow:0 18px 55px rgba(37,56,53,.09); }}
* {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:radial-gradient(circle at 8% 0%,#e3f0e9 0 23%,transparent 48%),linear-gradient(135deg,#f4efe4,#f7f5ef 52%,#e9f0ee); color:var(--ink); font:15px/1.65 "Avenir Next","Segoe UI",Arial,sans-serif; }}
.page {{ max-width:1180px; margin:0 auto; padding:26px 22px 70px; }}
header {{ position:relative; overflow:hidden; background:linear-gradient(125deg,#102e2d 0%,#155e58 58%,#286d69 100%); color:#fff; padding:44px 46px 42px; border-radius:28px; box-shadow:var(--shadow); }} header:after {{ content:""; position:absolute; width:390px; height:390px; right:-120px; top:-230px; border:1px solid rgba(255,255,255,.2); border-radius:50%; box-shadow:0 0 0 35px rgba(255,255,255,.04),0 0 0 70px rgba(255,255,255,.035); }}
.eyebrow {{ position:relative; z-index:1; color:#b9dfd5; text-transform:uppercase; letter-spacing:.16em; font:700 11px/1.2 "Avenir Next","Segoe UI",Arial,sans-serif; }} header h1 {{ position:relative; z-index:1; max-width:800px; font:700 clamp(36px,6vw,68px)/.98 "Iowan Old Style",Palatino,Georgia,serif; margin:14px 0 18px; letter-spacing:-.045em; }} header p {{ position:relative; z-index:1; max-width:760px; margin:0; color:#d8eee8; font-size:16px; }} .header-meta {{ position:relative; z-index:1; display:flex; flex-wrap:wrap; gap:9px; margin-top:24px; }} .header-meta span {{ border:1px solid rgba(255,255,255,.2); background:rgba(255,255,255,.09); border-radius:100px; padding:6px 11px; color:#e4f4ef; font-size:12px; }}
.report-nav {{ position:sticky; z-index:5; top:10px; display:flex; gap:7px; overflow:auto; margin:17px 0 20px; padding:7px; border:1px solid rgba(219,229,224,.85); border-radius:100px; background:rgba(255,253,248,.86); backdrop-filter:blur(12px); box-shadow:0 8px 28px rgba(37,56,53,.07); }} .report-nav a {{ white-space:nowrap; color:var(--muted); text-decoration:none; padding:7px 12px; border-radius:100px; font-size:12px; font-weight:700; }} .report-nav a:hover {{ background:var(--teal-soft); color:var(--teal-dark); }}
.report-section {{ margin:20px 0; padding:28px 30px; border:1px solid rgba(219,229,224,.9); border-radius:22px; background:rgba(255,253,248,.92); box-shadow:0 7px 32px rgba(37,56,53,.05); }} .section-heading {{ display:flex; align-items:baseline; gap:14px; margin-bottom:21px; }} .section-heading span,.panel-label,.decision-label {{ color:var(--teal); text-transform:uppercase; letter-spacing:.14em; font:800 10px/1.2 "Avenir Next","Segoe UI",Arial,sans-serif; }} h2 {{ margin:0; font:700 clamp(25px,3vw,34px)/1.05 "Iowan Old Style",Palatino,Georgia,serif; letter-spacing:-.03em; }} h3 {{ margin:23px 0 9px; font:800 15px/1.2 "Avenir Next","Segoe UI",Arial,sans-serif; }} p {{ margin:8px 0 15px; }} .muted,small {{ color:var(--muted); }}
.decision-section {{ padding:0; border:0; background:transparent; box-shadow:none; }} .decision-section .section-heading {{ display:none; }} .decision-layout {{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(280px,.75fr); gap:18px; }} .decision-main,.decision-reason {{ border-radius:20px; padding:27px 30px; }} .decision-main {{ color:#fff; background:var(--teal-dark); }} .decision-main .decision-label {{ color:#a9d8cd; }} .decision-main h2 {{ margin:12px 0 12px; color:#fff; font-size:clamp(27px,4vw,42px); }} .decision-main p {{ color:#d8eee8; max-width:730px; }} .decision-reason {{ display:flex; flex-direction:column; justify-content:space-between; background:var(--orange-soft); border:1px solid #f0c5a5; }} .decision-reason span {{ color:var(--orange); text-transform:uppercase; letter-spacing:.13em; font-size:10px; font-weight:800; }} .decision-reason strong {{ margin:16px 0; font:700 17px/1.3 "Iowan Old Style",Palatino,Georgia,serif; }} .decision-reason em {{ color:#80503b; font-size:12px; font-style:normal; }} .trigger-strip {{ display:grid; grid-template-columns:145px 1fr; gap:18px; align-items:center; margin-top:12px; padding:15px 19px; border:1px solid var(--line); border-radius:14px; background:rgba(255,253,248,.78); }} .trigger-strip span {{ color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.1em; }} .trigger-strip strong {{ font-size:13px; }}
.signal-grid,.two-col,.reception-split {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }} .signal-panel {{ padding:20px 22px; border-radius:16px; }} .signal-panel.positive {{ background:var(--teal-soft); border:1px solid #bfdfd6; }} .signal-panel.caution {{ background:var(--orange-soft); border:1px solid #f0c5a5; }} .signal-panel ul,.signal-panel ol {{ margin-bottom:0; }} .signal-panel li {{ margin:7px 0; }}
.community-section {{ background:linear-gradient(135deg,#f0f8f5,#fffdf8); border-color:#c7e2d9; }} .community-header {{ display:grid; grid-template-columns:1fr 1.4fr; gap:20px; align-items:end; }} .community-header h2 {{ margin:10px 0 5px; }} .community-header p {{ color:var(--muted); }} .community-facts .fact-grid {{ grid-template-columns:repeat(3,1fr); }} .community-reading {{ display:grid; grid-template-columns:1fr 1fr; gap:15px; margin:20px 0; }} .community-reading > div {{ padding:17px 18px; border-radius:14px; background:#fff; border:1px solid var(--line); }} .community-reading span {{ color:var(--teal); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.1em; }} .quote-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:13px; }} .quote-card {{ padding:18px; border:1px solid #c8ddd5; border-radius:15px; background:#fff; }} .quote-meta {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:12px; color:var(--muted); font-size:11px; }} .quote-meta span {{ padding:3px 7px; border-radius:100px; background:#edf5f1; }} .quote-card q {{ display:block; color:#273a38; font:italic 16px/1.45 "Iowan Old Style",Palatino,Georgia,serif; }}
.score-grid {{ display:grid; grid-template-columns:repeat(6,1fr); gap:11px; }} .metric {{ min-height:122px; padding:16px; border:1px solid #c9e3da; border-radius:15px; background:#f4fbf8; }} .metric.risk {{ border-color:#f0c5a5; background:var(--orange-soft); }} .metric.confidence {{ border-color:#c8d9e7; background:var(--blue-soft); }} .metric-top {{ display:flex; align-items:start; justify-content:space-between; gap:8px; }} .metric-top span {{ color:#4d6965; font-size:11px; font-weight:800; line-height:1.25; }} .metric-top strong {{ color:var(--teal-dark); font:800 26px/1 "Avenir Next","Segoe UI",Arial,sans-serif; }} .metric.risk .metric-top strong {{ color:#9a4a26; }} .metric-track {{ height:7px; overflow:hidden; margin:22px 0 9px; border-radius:10px; background:#d9e8e2; }} .metric-track i {{ display:block; height:100%; border-radius:10px; background:linear-gradient(90deg,#62a99a,#0f6b61); }} .metric.risk .metric-track i {{ background:linear-gradient(90deg,#e0a15d,#c76635); }} .metric-track i.unknown {{ width:100%; background:repeating-linear-gradient(135deg,#ccd8d4 0 5px,#e4ebe8 5px 10px); }} .metric small {{ font-size:11px; }}
.fact-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:10px; }} .fact-grid.compact {{ grid-template-columns:repeat(3,1fr); }} .fact {{ min-width:0; padding:13px 14px; border:1px solid var(--line); border-radius:12px; background:rgba(255,255,255,.58); }} .fact span {{ display:block; margin-bottom:5px; color:var(--muted); font-size:10px; font-weight:800; line-height:1.2; text-transform:uppercase; letter-spacing:.08em; }} .fact strong {{ display:block; overflow-wrap:anywhere; font-size:13px; line-height:1.35; }} .subsection {{ margin-top:21px; }}
.intent-callout {{ margin-top:19px; padding:18px 20px; border-left:4px solid var(--blue); border-radius:0 13px 13px 0; background:var(--blue-soft); }} .intent-callout .panel-label {{ color:var(--blue); }} .reception-card {{ padding:20px; border-radius:16px; border:1px solid var(--line); }} .reception-card.critic {{ background:#f6f2eb; }} .reception-card.community {{ background:var(--teal-soft); border-color:#c5e2d8; }} .reception-card p {{ font:700 19px/1.25 "Iowan Old Style",Palatino,Georgia,serif; }} .reception-card strong {{ color:var(--muted); font-size:12px; font-weight:600; }}
.action-section {{ border-color:#e8c5a9; background:linear-gradient(135deg,#fff7ee,#fffdf8); }} .action-card {{ padding:22px 24px; border:1px solid #efc39f; border-radius:16px; background:var(--orange-soft); }} .action-title {{ color:#8f421f; font:800 24px/1.15 "Iowan Old Style",Palatino,Georgia,serif; }} .action-card p {{ margin-bottom:0; }} .range-grid {{ margin-top:18px; }} .caveat {{ padding:14px 16px; border-radius:12px; background:#f8f4eb; color:#5f6962; }}
.table-wrap {{ overflow-x:auto; margin-top:12px; }} table {{ width:100%; border-collapse:collapse; font-size:13px; }} th,td {{ padding:13px 11px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} th {{ color:var(--muted); font-size:10px; letter-spacing:.1em; text-transform:uppercase; }} tr:last-child td {{ border-bottom:0; }} .source-list {{ padding-left:20px; }} .source-list li {{ margin:9px 0; }} a {{ color:var(--teal); text-underline-offset:3px; }} .badge {{ display:inline-block; padding:5px 9px; border-radius:100px; font-size:11px; font-weight:800; }} .badge.neutral {{ color:var(--teal-dark); background:var(--teal-soft); }}
.appendix-section {{ background:#f0f2ed; }} footer {{ margin-top:24px; color:var(--muted); text-align:center; font-size:11px; }}
@media (max-width:950px) {{ .score-grid {{ grid-template-columns:repeat(3,1fr); }} .decision-layout,.community-header {{ grid-template-columns:1fr; }} }} @media (max-width:680px) {{ .page {{ padding:14px 10px 45px; }} header {{ padding:31px 24px; border-radius:21px; }} .report-section {{ padding:22px 18px; border-radius:17px; }} .section-heading {{ display:block; }} .section-heading span {{ display:block; margin-bottom:8px; }} .signal-grid,.two-col,.reception-split,.community-reading,.quote-grid {{ grid-template-columns:1fr; }} .score-grid {{ grid-template-columns:repeat(2,1fr); }} .community-facts .fact-grid,.fact-grid.compact {{ grid-template-columns:1fr; }} .trigger-strip {{ grid-template-columns:1fr; gap:4px; }} .report-nav {{ border-radius:14px; }} }}
</style>
</head>
<body><main class="page">
<header><div class="eyebrow">Game sentiment checker l30d / one-game report</div><h1>{esc(game)}</h1><p>Public-data launch sense-check for game-key inventory decisions.</p><div class="header-meta"><span>{esc(phase)}</span><span>Steam AppID {esc(snapshot.get('steam_appid'))}</span><span>Captured {esc(captured)}</span></div></header>
<nav class="report-nav" aria-label="Report navigation"><a href="#decision">Decision</a><a href="#community">Community</a><a href="#scores">Scores</a><a href="#reception">Reception</a><a href="#inventory">Inventory</a><a href="#coverage">Evidence</a></nav>
{sections}
<footer>Generated by Game sentiment checker l30d · Public evidence only · Data captured {esc(captured)}</footer>
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
