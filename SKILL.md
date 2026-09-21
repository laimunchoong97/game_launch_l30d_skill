---
name: game-sentiment-checker-l30d
description: Research upcoming or recently released video games using public online data and produce a full launch sense-check for inventory decisions. Use whenever the user asks about game launch reception, Steam demand, preloading game keys, upfront key purchasing, likely sales, launch risk, player sentiment, game hype, or which releases are safest to stock. The skill combines public Steam facts, SteamDB context, last30days community research, aspect-based sentiment, purchase-intent analysis, comparable releases, price/markdown risk, confidence scoring, and a buy posture. It does not invent exact reseller sales or private wishlist data.
---

# Game sentiment checker l30d

Produce a complete, evidence-led sense-check for exactly one upcoming or recently released game. The final deliverable is a self-contained, formatted HTML report. The report is for public-data market assessment and inventory posture, not an exact forecast of a specific reseller's key sales.

## Operating principles

- Resolve the exact game, platform, region, Steam AppID, developer, publisher, and release phase before researching.
- Accept and research one game per run. If the user supplies multiple games, ask them to choose one rather than silently batching or combining reports.
- Use public sources only. Never request, store, or expose Steam credentials, cookies, tokens, or private publisher data.
- Separate demand potential, purchase intent, momentum, reception health, market/markdown risk, and evidence confidence.
- Treat missing data as unknown and reduce confidence; never convert missing data into a zero-demand conclusion.
- Use sentiment as aspect-based evidence, not as a raw positive/negative percentage.
- Distinguish attention from purchase intent. Explicit launch-buy, preorder, sale-wait, patch-wait, refund, and avoidance signals matter more than generic praise.
- Cite every material finding with its source and capture date. Do not claim a source was quiet when it was unavailable, rate-limited, or incomplete.
- Use ranges and buy postures where public data cannot support a defensible unit estimate.
- Keep the final HTML self-contained: inline CSS, no external fonts, no external JavaScript, and no unescaped research text.

## Modes

Choose the least expensive mode that answers the request:

- **Quick:** structured Steam facts plus a focused public pulse for screening. Target 2-5 minutes.
- **Standard:** full 30-day social/web pulse, sentiment, intent, comparables, price risk, and the complete report. Target 8-15 minutes.
- **Deep:** standard research plus multiple comparables, public sales evidence, detailed trend analysis, and evidence reconciliation. Target 15-30 minutes.

Use Standard by default. Quick still produces the full HTML report but leaves more fields marked unavailable. Deep is for a title with meaningful upfront exposure or conflicting evidence. Do not use this skill to batch a list; run one report per game.

## Data collection order

1. Run `scripts/steam_public.py` with a Steam AppID or title. It collects public app metadata, price, review summary, recent review summary, and current players. Treat failures as source-status events.
2. Search SteamDB public pages for followers, follower momentum, price history, release-state changes, player context, packages, and editions. SteamDB is a third-party context source, not official sales data.
3. Use the existing `last30days` skill/engine when installed for the 30-day community pulse. Generate a named-entity plan and use Reddit, YouTube, X, and web lanes according to their availability. If `last30days` is unavailable, use the configured web-search providers and clearly mark the reduced coverage.
4. Search for publisher-confirmed sales, investor reports, launch milestones, creator coverage, reputable reviews, and comparable releases.
5. Normalize the evidence, deduplicate repeated items, classify sentiment and purchase intent, then score.

## Optional integrations

The skill must work without user-provided keys. Detect optional integrations from environment variables and skip unavailable connectors without failure.

Supported optional configuration includes:

- `LAST30DAYS_SKILL_DIR`, `LAST30DAYS_PYTHON`, `LAST30DAYS_MEMORY_DIR` for the existing last30days engine.
- `BRAVE_API_KEY`, `SERPER_API_KEY`, `EXA_API_KEY`, or `PARALLEL_API_KEY` for richer web search when host search is unavailable.
- Existing last30days X, YouTube, Reddit, TikTok, and Instagram configuration. Do not duplicate or expose its cookie handling.
- `YOUTUBE_API_KEY` for optional stable YouTube metadata; yt-dlp remains an acceptable fallback.
- `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` for optional Twitch metrics.
- `STEAM_API_KEY` only for optional Steam endpoints that require it. The public MVP endpoints do not require it.
- Optional third-party sales sources may be added through documented URLs or adapters, but estimated owners/sales must remain labeled as estimates.

Never put keys in this file, reports, examples, tests, Git history, or command arguments. Use `.env.example` as a names-only reference.

## Scoring

Read `references/scoring-model.md` before scoring. For pre-launch games, score audience/intent, momentum, developer pull, comparable performance, creator/community activity, price fit, and release competition. For released games, replace pre-launch proxies with reviews, review velocity, player trends, public sales evidence, price decay, and sustained sentiment.

Calculate scores only from available evidence, renormalizing weights when fields are missing. Report the coverage and confidence separately from the score.

At minimum, calculate:

```text
Demand potential:       00/100
Purchase intent:        00/100
Launch momentum:        00/100
Reception health:       00/100
Market/markdown risk:   00/100  (higher is worse)
Evidence confidence:    Low / Medium / High
Overall posture:        Large controlled buy / Moderate buy / Test buy / Wait / Avoid preload
```

Use the following interpretation unless the evidence explains a different conclusion:

- 80-100: strong opportunity, but still cap exposure by markdown risk.
- 65-79: promising, controlled buy.
- 50-64: uncertain, test allocation.
- 35-49: weak or high-risk, wait for launch evidence.
- Below 35: avoid significant preload.

## Sentiment and intent analysis

Classify public items by:

- Sentiment: positive, neutral, negative, mixed.
- Intent: preorder/launch buy, interested/waiting for reviews, sale wait, patch wait, avoid, refund, already played, or general discussion.
- Aspect: gameplay, performance, price, content, story, multiplayer, monetization, DRM/platform, developer trust, early access, and support.
- Severity: temporary launch friction or structural demand risk.

Report the hype-to-intent gap: high awareness or praise with weak launch-buy intent is a preload warning. Track direction across 30 days, 7 days, 72 hours, and 24 hours when available. Flag review bursts, review bombing, copied wording, free-weekend effects, and influencer spikes instead of treating them as ordinary reception.

## Required full HTML report

Read `references/report-template.md` and use it in full. Do not replace it with a short summary. Every mode produces the same complete HTML section structure; Quick mode may contain more unavailable fields. Render the normalized report data with `scripts/render_report.py` and return the generated `.html` file path. Include:

- Decision snapshot
- Executive recommendation
- Score breakdown
- Demand evidence
- Purchase-intent analysis
- Sentiment and reception analysis
- Comparable games
- Price and markdown risk
- Public sales and player evidence
- Inventory recommendation
- Reorder and stop signals
- Evidence and coverage

The report must state which evidence is confirmed, estimated, inferred, unavailable, or degraded. It must not provide a precise key quantity unless the public comparable baseline and all assumptions are shown. Otherwise provide a buy posture and a conditional low/base/high range.

The HTML must contain:

- A clear title and data-capture timestamp.
- Score cards for demand, purchase intent, momentum, reception, market/markdown risk, and confidence.
- All twelve sections in `references/report-template.md`.
- Source links beside material findings where URLs are available.
- Visible unavailable/partial-source notes.
- Responsive layout suitable for desktop and mobile.

Do not make the HTML depend on a browser extension, local JavaScript bundle, external stylesheet, or secret-bearing URL.

## Local scripts

Use `scripts/steam_public.py` for keyless public Steam facts. Use `scripts/score_release.py` for reproducible weighted scoring when a normalized signal JSON is available. Use `scripts/render_report.py --input report.json --output report.html` to produce the final self-contained HTML report. Run `python -m unittest discover -s tests` before publishing changes to this skill.
