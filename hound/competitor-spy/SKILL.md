---
name: competitor-spy
description: >
  Deep-dive a competitor's shop or listing to extract pricing, visual style, review insights,
  and positioning gaps. Use when the user wants to analyze a specific competitor, reverse-engineer
  a successful shop, or find weaknesses to exploit. Triggers: "竞品分析", "看一下这个店",
  "competitor", "spy", "这个店怎么做的", "reverse engineer", "对手分析".
---

# Competitor Spy

**Spy** on a competitor shop or listing and return actionable gaps — what they do well, where
they're weak, and what angle beats them.

## Input

User provides one of:
- An Etsy shop URL: `https://www.etsy.com/shop/ShopName`
- An Etsy listing URL: `https://www.etsy.com/listing/...`
- A shop name: `"ShopName"`

If not provided, ask before proceeding.

## Steps

### 1. Fetch shop and top listings

```bash
# Shop overview — reviews, sales count, about section
opencli browser main open "https://www.etsy.com/shop/<ShopName>"
opencli browser main extract

# Top listings — titles, prices, review counts
opencli browser main open "https://www.etsy.com/shop/<ShopName>?sort_on=most_recent"
opencli browser main extract

# Reviews page — what buyers praise and complain about
opencli browser main open "https://www.etsy.com/shop/<ShopName>/reviews"
opencli browser main extract
```

### 2. Extract signals

**Shop-level**
- Total sales and review count → shop authority
- About section language → brand positioning and story angle
- Price range across listings → target customer tier

**Listing-level** (top 5 by relevance)
- Title structure → keyword strategy
- Main image style → visual positioning (lifestyle / flat lay / model / minimal)
- Price point and variations offered

**Reviews** (scan top 20)
- Recurring praise → what buyers value most → double down on this
- Recurring complaints or missing mentions → gap to exploit
- Specific product features mentioned → real differentiators

### 3. Output the spy report

```
## 🔍 Competitor Spy — [ShopName]

### shop snapshot
[Sales count, review score, price range, positioning in one sentence]

### what they do well
[2–3 things buyers consistently praise — these are table stakes to match]

### gaps and weaknesses
[2–3 complaints or missing elements from reviews — these are your entry points]

### visual style
[Main image approach: lifestyle / flat lay / model / minimal + dominant colors/mood]

### keyword angle
[How they title listings — what keywords they own vs what they miss]

### how to beat them
[One concrete positioning move: price, style, story, or niche angle]
```

Report is complete when all six sections are filled and "how to beat them" is a single
concrete action, not a vague suggestion.
