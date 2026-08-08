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

# Instagram — visual style trends via hashtag page
opencli browser main open "https://www.instagram.com/explore/tags/<keyword_no_spaces>/"
opencli browser main extract

# Etsy — top listings, pricing, competition density
opencli browser main open "https://www.etsy.com/search?q=<keyword>&sort_on=score"
opencli browser main extract
```

Run Reddit and browser opens simultaneously. Extract after each browser open.
A scout is complete when all three return output.

### 2. Extract signals

From each source pull only what changes the decision:

**Reddit**
- Top recurring questions or complaints → buyer pain points
- Posts with high score + high comments → validated demand
- Subreddits where the topic lives → where buyers gather

**Instagram**
- Dominant visual styles in post alt-text and captions → aesthetic direction
- Post density on the hashtag page → niche size and activity level

**Etsy**
- Product titles of top listings → winning keywords and positioning angles
- Ad vs organic ratio → competition intensity
- Price range across top results → viable price points

### 3. Output the scout report

Deliver a single structured report. Every section must be filled — no "N/A" or "data unavailable"
without a reason.

```
## 🐕 Market Scout — [keyword]

### verdict
[One sentence: enter / pass / enter with angle X]

### demand signals
- Reddit: [top subreddits + strongest posts]
- Instagram: [hashtag activity + dominant visual style]
- Etsy: [top listing titles + price range]

### buyer pain points
[3–5 bullet points from Reddit discussions]

### winning angle
[What style, price point, or positioning has the least competition and the most demand]

### risks
[Saturation level, seasonality, or platform-specific hazards]
```

The report is complete when all five sections are present and the verdict is a single actionable
sentence.

## Handoff → Parrot

After the scout report is done, pass these three things to `parrot/brand-story` or `parrot/product-copy`:

```
Winning angle:   [one line from scout report]
Buyer pain points: [top 2–3 bullets]
Price point:     [validated range from Etsy]
```

This gives Parrot the market context it needs to write on-target copy without guessing.

## Notes

**Reddit**: works without login.

**Instagram**: uses `opencli browser` to fetch public hashtag pages — no login required.
For deeper profile data, optionally run:
```bash
opencli browser main open "https://www.instagram.com/<top_account>/"
opencli browser main extract
```

**Etsy**: uses `opencli browser` to fetch public search results — no token required.
