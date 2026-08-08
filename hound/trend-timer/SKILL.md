---
name: trend-timer
description: >
  Detect seasonality and timing signals for a product category using Reddit post history and
  Etsy listing data. Use when the user wants to know the best time to launch, whether a niche
  is trending up or cooling down, or how to time inventory. Triggers: "时机", "季节性",
  "什么时候上架", "trend timing", "seasonality", "when to launch", "is this trending".
---

# Trend Timer

**Time** a product category — when does demand peak, is it rising or falling, and when should
you launch?

## Input

User provides a **category keyword**. Same format as market-scout.

If not provided, ask before proceeding.

## Steps

### 1. Collect timing signals in parallel

```bash
# Reddit — post timestamps reveal when buyers talk about this (seasonal spikes)
opencli reddit search "<keyword>" --limit 50 -f yaml

# Etsy search sorted by most recent — what's being listed now vs older listings
# Note: Etsy may ignore sort_on=date_desc and return score-ranked results anyway.
# If both extracts look identical, treat the combined result as top listings only
# and rely on Reddit timestamps as the primary recency/trend signal.
opencli browser main open "https://www.etsy.com/search?q=<keyword>&sort_on=date_desc"
opencli browser main extract

# Etsy search sorted by top — what has accumulated the most reviews over time
opencli browser main open "https://www.etsy.com/search?q=<keyword>&sort_on=score"
opencli browser main extract
```

### 2. Extract timing signals

**Reddit timestamps**
- Group posts by month using `created_utc` field
- Identify months with clustering → seasonal demand peaks
- Check if recent posts (last 3 months) outnumber older ones → rising or fading trend

**Etsy recent listings**
- What styles and keywords appear in newest listings → what sellers are betting on now
- New shop names vs established shops listing this → entry competition heating up

**Etsy top listings**
- Review accumulation dates on best sellers → how long it takes to build authority in this niche
- Price drift between older top sellers and newer ones → market maturing or expanding

### 3. Output the timing report

```
## ⏱ Trend Timer — [keyword]

### trend direction
[Rising / Stable / Cooling — one sentence with evidence]

### peak season
[Month range when demand spikes, based on Reddit post clustering]

### launch window
[Best time to list new products to catch the demand curve]

### competition timing
[Are new sellers flooding in now, or is the window still open]

### recommendation
[Launch now / Wait until [month] / Skip this cycle — one actionable sentence]
```

Report is complete when all five sections are filled and the recommendation names a
specific action or timeframe.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "hound": {
    "trend": {
      "direction": "rising | stable | cooling",
      "peak_months": ["month1", "month2"],
      "launch_window": "description of best timing",
      "recommendation": "launch now | wait until [month] | skip this cycle"
    }
  }
}
```
