# Game sentiment checker l30d

An online-data research skill for sense-checking upcoming and recently released game launches. It produces a full report covering demand, purchase intent, momentum, sentiment, comparable releases, markdown risk, confidence, and an upfront-buy posture.

It is designed for game-key inventory decisions. It does not claim to know exact reseller sales, private Steam wishlist counts, or regional key demand.

## What it uses

- Public Steam endpoints for metadata, price, reviews, and current players
- SteamDB public pages for supplementary followers, price-history, release-state, and player context
- The existing `last30days` engine for 30-day Reddit, YouTube, X, and web research when installed
- Public publisher announcements, investor reports, industry coverage, and comparable releases
- Optional web-search and platform integrations configured through environment variables

## No-key baseline

The skill is usable without user-provided credentials. Optional providers are detected at runtime and skipped when unavailable. Missing sources lower confidence; they are not interpreted as evidence of weak demand.

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

The required full report structure is in `references/report-template.md`. The skill should use that template for Standard and Deep runs.

## Optional integrations

Supported optional environment variables are documented in `.env.example`. The skill can use a configured Brave, Serper, Exa, or Parallel search provider; an existing `last30days` installation; YouTube API or yt-dlp; Twitch credentials; and optional Steam API access. No optional integration is required for the baseline.

## Tests

```powershell
python -m unittest discover -s tests
```
