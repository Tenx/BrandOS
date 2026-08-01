---
name: market-scout
description: >
  Cross-border product research via Reddit, Instagram, and Etsy. Use when the user wants to
  validate a product niche, find buyer pain points, spot trending styles, or decide whether a
  category is worth entering. Triggers: "调研", "选品", "市场验证", "这个品类能做吗",
  "scout", "research niche", "trending", "what's selling".
---

# Market Scout

**Scout** a product category across three platforms and surface a decision-ready signal: is this
worth selling, and what angle wins?

## Input

User provides a **category keyword** — English or Chinese, broad or specific.
Examples: `"crochet top"`, `"手工蜡烛"`, `"macrame wall hanging"`.

If the user hasn't provided one, ask for it before proceeding.

## Steps

### 1. Run three scouts in parallel

```bash
# Reddit — buyer discussions, pain points, demand signals
opencli reddit search "<keyword>" --limit 20 -f yaml

# Instagram — visual style trends, top accounts in the niche
opencli instagram search "<keyword>" -f yaml

# Etsy — real listing data, pricing, competition density
python3 ~/.agents/skills/market-scout/scripts/etsy_scout.py "<keyword>"
```

Run all three simultaneously. A scout is complete when all three commands return output or a
clear error.

### 2. Extract signals

From each source pull only what changes the decision:

**Reddit**
- Top recurring questions or complaints → buyer pain points
- Posts with high score + high comments → validated demand
- Subreddits where the topic lives → where buyers gather

**Instagram**
- Account names and follower counts from search results → niche size
- Run `opencli instagram user <top_account> -f yaml` on the 2-3 highest-ranked accounts → recent
  post themes, engagement patterns, visual style

**Etsy**
- Price range of top listings
- Review count on best sellers → demand volume
- Gap: what's missing or low-quality in current supply

### 3. Output the scout report

Deliver a single structured report. Every section must be filled — no "N/A" or "data unavailable"
without a reason.

```
## 🐕 Market Scout — [keyword]

### verdict
[One sentence: enter / pass / enter with angle X]

### demand signals
- Reddit: [top subreddits + strongest posts]
- Instagram: [top account + follower count + dominant visual style]
- Etsy: [price range, review volume on top sellers]

### buyer pain points
[3–5 bullet points from Reddit discussions]

### winning angle
[What style, price point, or positioning has the least competition and the most demand]

### risks
[Saturation level, seasonality, or platform-specific hazards]
```

The report is complete when all five sections are present and the verdict is a single actionable
sentence.

## Platform notes

**Reddit login**: `opencli reddit search` works without login. If it returns AUTH_REQUIRED,
run `opencli reddit login` first.

**Instagram login**: required. If commands return HTTP 400, run `opencli instagram login` first,
then re-run the scout.

**Etsy**: uses the `etsy-listing-manager` skill's OAuth token. If not configured, run the OAuth
setup from `rabbit/etsy-listing-manager` first.
