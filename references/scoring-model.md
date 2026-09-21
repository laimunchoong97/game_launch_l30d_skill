# Scoring model

## Pre-launch score

| Category | Weight | Evidence logic |
|---|---:|---|
| Audience size and intent | 20 | Followers, disclosed wishlists, preorders, active community size |
| Momentum | 20 | Follower, search, trailer, creator, and discussion growth |
| Developer/franchise pull | 15 | Prior audience, sales milestones, reviews, and trust |
| Comparable performance | 20 | Closely matched public launch outcomes |
| Creator/community attention | 10 | YouTube, Twitch, Reddit, X, previews, and coverage |
| Price/product fit | 10 | Price, discount, platform fit, and audience willingness to pay |
| Release competition | 5 | Similar titles or major releases in the same window |

## Post-launch score

| Category | Weight | Evidence logic |
|---|---:|---|
| Review score and velocity | 20 | Buyer satisfaction and word of mouth |
| Concurrent-player performance | 15 | Launch engagement and decay |
| Public sales evidence | 20 | Confirmed milestones first; third-party estimates labeled |
| Demand momentum | 15 | Whether interest is accelerating or fading |
| Community sentiment | 10 | Repeated praise, complaints, refunds, and support concerns |
| Price/discount behavior | 10 | Markdown and bundle risk |
| Competitive pressure | 10 | Substitutes and overlapping releases |

## Scoring rules

Score each available metric from 0 to 5, then calculate:

```text
weighted score = metric score / 5 * category weight
```

If a category is unavailable, exclude it from the numerator and renormalize the remaining weights. Record the missing category and lower confidence. Never treat missing wishlist or sales data as zero demand.

## Confidence

- High: independent sources agree, direct platform or publisher evidence exists, and the title is released or has close comparables.
- Medium: several proxy sources agree, but sales or wishlist data is estimated or the game is unreleased.
- Low: evidence is mostly social attention, a new IP has no close comparables, or source coverage is partial.

## Buy posture

Demand score alone does not determine quantity. Combine it with markdown risk, evidence confidence, and replenishment assumptions. Use a posture when the channel share is unknown:

- Strong demand + low/medium risk: large controlled buy.
- Strong demand + high risk or medium confidence: moderate buy.
- Medium demand or thin evidence: test buy.
- Weak demand, deteriorating reception, or high markdown risk: wait or avoid preload.
