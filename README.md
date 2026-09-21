# Game sentiment checker l30d

An online-data research skill for sense-checking one upcoming or recently released game at a time. It produces a self-contained HTML report covering demand, purchase intent, momentum, sentiment, comparable releases, markdown risk, confidence, and an upfront-buy posture.

It is designed for game-key inventory decisions. It does not claim to know exact reseller sales, private Steam wishlist counts, or regional key demand.

## What it uses

The skill combines several public-data layers:

- Public Steam endpoints for metadata, price, reviews, and current players
- SteamDB public pages for followers, price history, release-state changes, packages, editions, and player context
- The existing `last30days` engine for 30-day Reddit, YouTube, X, and web research when installed
- Public publisher announcements and investor reports
- Gaming publications, professional reviews, creator coverage, and comparable releases
- Optional web-search, social, video, streaming, and Steam integrations

## No-key baseline

The skill is usable without user-provided credentials. Optional providers are detected at runtime and skipped when unavailable. Missing sources lower evidence confidence; they are not interpreted as evidence of weak demand.

The no-key baseline uses:

- Public Steam endpoints
- Public SteamDB pages through available web access
- Public Reddit and web research
- Any host-provided WebSearch capability
- Local deterministic scoring and HTML rendering

Copy `.env.example` to a local environment file only if needed. Never commit real secrets.

## Local public Steam facts

```powershell
python scripts/steam_public.py --query "Example Game" --country us --out research-output/example.json
python scripts/steam_public.py --appid 570 --out research-output/dota2.json
```

The collector uses public endpoints and returns source-status fields. It does not use Steam credentials or undocumented SteamDB APIs.

## Score a normalized evidence bundle

```powershell
python scripts/score_release.py --input evidence.json --output score.json
```

See `references/scoring-model.md` for the categories and missing-data rules.

## Report

The required full report structure is in `references/report-template.md`. Every run produces all sections in a formatted HTML file. The renderer is self-contained and escapes research text before inserting it into HTML.

```powershell
python scripts/render_report.py --input report.json --output research-output\example-sense-check.html
```

Only one game is accepted per report. If you need to assess several games, run the skill once for each title.

## Optional integrations

All optional integrations are environment-variable-driven. The skill should continue running when any optional source is unavailable and should mark that source as unavailable or degraded in the final HTML report.

### Existing `last30days` engine

```text
LAST30DAYS_SKILL_DIR
LAST30DAYS_PYTHON
LAST30DAYS_MEMORY_DIR
```

These variables configure the existing `last30days` research engine:

- `LAST30DAYS_SKILL_DIR` points to the installed `last30days` skill directory.
- `LAST30DAYS_PYTHON` selects the Python interpreter used to run its engine. The default is `python3`.
- `LAST30DAYS_MEMORY_DIR` selects the directory for saved research, cache, library, and report artifacts.

When available, the existing engine adds a 30-day community pulse to the structured Steam facts.

### Web-search providers

Configure one of these providers when the host does not already expose a suitable WebSearch tool:

```text
BRAVE_API_KEY
SERPER_API_KEY
EXA_API_KEY
PARALLEL_API_KEY
```

They can improve discovery and corroboration for:

- SteamDB pages
- Publisher announcements
- Investor reports
- Comparable game launches
- Sales milestones
- Gaming publications
- Professional reviews
- Creator coverage
- Price and discount news
- Release-window competition

The skill does not require all four providers. Configure one provider and use the others as fallbacks only if the host supports that configuration.

### Steam API

```text
STEAM_API_KEY
```

The public MVP collector does not require this key. It already uses public endpoints for:

- App metadata
- Developer and publisher
- Release date
- Genre
- Platform support
- Price and discount
- Review summary
- Recent reviews
- Current player count

An optional Steam API key may support additional Steam endpoints in future versions, but it does not provide:

- Exact game sales
- Private wishlist counts
- Reseller key sales
- Regional key demand
- Your store's conversion rate

### YouTube

```text
YOUTUBE_API_KEY
```

Optional uses include:

- Trailer discovery
- Review and preview discovery
- Creator coverage
- Channel metadata
- View and engagement metadata
- Recent video momentum

`yt-dlp` can be used as a fallback, so a YouTube API key is not mandatory.

### Twitch

```text
TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET
```

Optional uses include:

- Streamer coverage
- Viewer counts
- Game-category activity
- Launch streaming momentum
- Creator interest

### Existing `last30days` social connectors

When the existing `last30days` engine is installed and configured, it may provide the following additional source lanes.

#### Reddit

Useful for:

- Player intent
- Game-specific subreddit discussions
- Purchase objections
- Refund signals
- Patch-wait signals
- Price concerns
- Performance complaints
- Recurring community themes

#### X/Twitter

Useful for:

- Developer announcements
- Publisher activity
- Launch reactions
- Influencer commentary
- Player sentiment
- Community disputes
- Price and performance discussion

X access may require browser cookies, API access, or an existing configured X backend. The skill must not request or store cookies itself.

#### YouTube through `last30days`

Useful for:

- Trailers
- Reviews
- Previews
- Creator opinions
- Comments
- View momentum

The engine may use `yt-dlp` or a configured YouTube backend.

#### TikTok

Useful for:

- Viral awareness
- Short-form creator activity
- Meme momentum
- Audience reaction

This generally requires the existing `last30days` TikTok configuration or a supported third-party provider.

#### Instagram

Useful for:

- Publisher activity
- Creator activity
- Visual launch campaigns
- Audience response
- Promotional momentum

This generally requires the existing `last30days` Instagram configuration.

### Other inherited `last30days` sources

The existing engine supports additional connectors that may be useful in specific circumstances:

| Source | Potential use for game-release research |
|---|---|
| Hacker News | Game technology, engines, development tooling, or open-source game projects |
| GitHub | Open-source game projects, repositories, issues, releases, and developer activity |
| Polymarket | Delay, launch, or event-related prediction markets when a relevant market exists |
| Bluesky | Public game discussion and developer/player reactions |
| Truth Social | Public discussion when relevant to a publisher, personality, or event |
| Digg | Trending public discussion when the source is configured |
| arXiv | Technical research related to game AI, graphics, or simulation |
| Techmeme | Game technology or major industry stories |
| Dripstack | Additional research or social coverage when configured |
| Perplexity | Optional web-grounded research when configured |
| LinkedIn | Studio hiring, publisher investment, and industry signals |
| Trustpilot | Store, marketplace, or platform reputation |
| Xiaohongshu | Chinese-language player and audience sentiment |
| Threads | Public social discussion |
| Pinterest | Low-priority visual attention signals |
| Stocktwits | Financial discussion for publicly traded publishers when applicable |
| Jobs | Studio hiring and expansion or contraction signals |
| Corpus | Local private research files when explicitly configured |
| Grounding | General web evidence and search results |

These are inherited capabilities of `last30days`, not all standalone collectors bundled in this repository.

### Optional third-party sales sources

The skill may use public pages or documented adapters for estimated sales and ownership sources such as:

- VG Insights
- Gamalytic
- SteamSpy
- PlayTracker
- GameDiscoverCo
- Circana
- GSD
- Newzoo

These sources must be labeled as confirmed, estimated, or proxy evidence. Third-party estimates must never be presented as exact sales, and a source must not be treated as authoritative merely because it returns a precise-looking number.

## Integration behavior and limitations

The current repository directly includes:

- Public Steam data collection in `scripts/steam_public.py`
- Reproducible scoring in `scripts/score_release.py`
- Self-contained HTML rendering in `scripts/render_report.py`

The external web-search providers, Twitch, YouTube API, X, TikTok, Instagram, and broader `last30days` connectors are optional runtime integrations. They are consumed by the host environment or the installed `last30days` engine rather than bundled as hard-coded secret-bearing clients.

No integration can reliably expose:

- Your store's game-key sales
- Reseller-channel conversion rates
- Private Steam wishlist counts for games you do not own
- Exact total sales for most games
- Regional key demand
- Supplier replenishment speed

These limitations must appear in the report's evidence and coverage section.

## Tests

```powershell
python -m unittest discover -s tests
```
