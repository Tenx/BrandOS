---
name: audience-finder
description: >
  Identify the best target audience for a product across ad platforms. Outputs buyer persona,
  interest targeting keywords, exclusion audiences, and platform priority ranking — ready to
  plug into Meta Ads, TikTok Ads, Pinterest Ads, or Google Shopping.
  Use when the user wants to know who to target before launching ads.
  Triggers: "受众", "目标人群", "targeting", "audience", "投给谁", "人群定向",
  "interest targeting", "受众定位", "who to target".
---

# Audience Finder

Define who to target before spending a dollar. Outputs platform-ready audience parameters
and a ranked list of where to find this buyer most efficiently.

## Input

User provides:
- **Product** — what they sell (paste from product-copy, or describe)
- **Price point** — helps determine platform fit (budget / mid / premium)
- **Current sales channel** — Etsy / Shopify / Amazon / Ozon / other
- **Any known buyer info** (optional) — age, gender, location, interests if already known

If product is missing, ask before proceeding.

## Steps

### 1. Build buyer persona

From product inputs, define the core buyer in 4 dimensions:

**Demographics**
- Age range, gender skew
- Geography: primary markets (US / UK / DE / AU / CA most common for cross-border)
- Household context: lives alone / family / homeowner

**Psychographics**
- Values and identity (e.g. "buys handmade to avoid fast fashion")
- Purchase trigger (gift / self-treat / home refresh / seasonal)
- Price sensitivity signal (impulse at $20 / considered at $50 / researched at $100+)

**Behavioral signals**
- What else do they buy? (adjacent brands and categories)
- Where do they discover products? (search / social scroll / Pinterest save)
- When do they buy? (seasonal peaks from trend-timer if available)

**Negative persona** — who NOT to target
- Characteristics that indicate low conversion (e.g. deal-hunters if premium product)

### 2. Map to platform targeting parameters

For each relevant platform, output specific targeting parameters:

**Meta (Facebook + Instagram)**
- Detailed interests: list 8–12 specific interest categories
- Lookalike seed: describe the ideal seed audience (e.g. "website purchasers", "email list")
- Exclusions: audiences to exclude
- Placement recommendation: Feed / Reels / Stories / Shopping

**Pinterest**
- Interest categories (Pinterest taxonomy)
- Keywords for keyword targeting (Pinterest is search-driven)
- Audience type: browse / search / actalike
- Board topics to target

**TikTok**
- Interest categories
- Hashtag audiences (content users engage with)
- Creator lookalike signals (describe creator profile type, not specific handles)
- Device/behavior: note if product skews iOS vs Android buyers

**Google Shopping** (for Shopify/WooCommerce sellers)
- Audience signals for Performance Max: describe in-market segments
- Negative keywords to exclude irrelevant traffic

### 3. Platform priority ranking

Score each platform 1–5 for this specific product based on:
- Buyer presence (is this audience active here?)
- Product-format fit (visual product → Pinterest/Instagram; impulse → TikTok)
- CPC efficiency at this price point
- Competition density

Output ranked recommendation with one-line rationale per platform.

## Output

```
## 🎯 Audience Finder — [Product]

### buyer persona
Demographics: [age, gender, geo]
Psychographics: [values, trigger, price sensitivity]
Behavioral: [adjacent brands/categories, discovery channel, timing]
Negative: [who to exclude]

### meta targeting
Interests: [8–12 specific interests]
Lookalike seed: [description]
Exclusions: [audience exclusions]
Placement: [recommended placements]

### pinterest targeting
Interest categories: [list]
Keywords: [10–15 search keywords]
Audience type: [browse / search / actalike]

### tiktok targeting
Interest categories: [list]
Hashtag audiences: [content signals]
Behavioral note: [any device/behavior flags]

### google shopping signals
In-market segments: [description]
Negative keywords: [list]

### platform priority
1. [Platform] — [one-line rationale] — ROAS potential: [High/Med/Low]
2. [Platform] — ...
3. [Platform] — ...
4. [Platform] — ...

### recommended first platform
[Single recommendation for where to start, with budget threshold]
```

Report is complete when buyer persona and at least 2 platform targeting sections are filled,
and platform priority list names a clear #1 recommendation.
