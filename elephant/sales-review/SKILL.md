---
name: sales-review
description: >
  Analyze shop sales data to identify best sellers, underperformers, and revenue trends.
  Pulls data from Etsy Stats, Amazon Seller Central, or Shopify Analytics via opencli browser,
  then outputs an actionable weekly/monthly review with specific next steps.
  Use when the user wants to understand what's working, what to restock, or what to cut.
  Triggers: "复盘", "销售数据", "数据分析", "sales review", "哪个产品卖得好",
  "revenue review", "店铺数据", "什么产品滞销", "weekly review", "monthly review".
---

# Sales Review

Pull shop data → identify winners and losers → output ranked action list.
Works with Etsy, Amazon Seller Central, and Shopify.

## Input

User provides:
- **Platform** — Etsy / Amazon / Shopify (default: ask which platform)
- **Period** — last 7 days / 30 days / 90 days (default: 30 days)
- **Focus** (optional) — revenue / units / ROAS / returns — what to prioritize in analysis

## Steps

### 1. Pull data via browser

**Etsy Stats:**
```bash
opencli browser main open "https://www.etsy.com/your/stats"
opencli browser main extract
# If paginated or JS-rendered, use find to locate data tables:
opencli browser main find --css "table, [data-stats], .stats-row"
```

**Amazon Seller Central — Business Reports:**
```bash
opencli browser main open "https://sellercentral.amazon.com/business-reports/ref=xx_sitemetric_cont_home"
opencli browser main extract
```

**Shopify Analytics:**
```bash
opencli browser main open "https://<shop>.myshopify.com/admin/analytics"
opencli browser main extract
# Or via Admin API:
GET /admin/api/2024-01/orders.json?status=any&created_at_min=<date>&fields=id,total_price,line_items,refunds
```

Extract: revenue per SKU, units sold, views, conversion rate, refund rate, ad spend if available.

### 2. Classify products into tiers

**Tier A — Stars:** High revenue + high conversion rate → protect, restock, consider scaling ads
**Tier B — Potential:** High views but low conversion → listing or pricing problem, needs fix
**Tier C — Stable:** Steady low-volume sellers → maintain, no action needed
**Tier D — Dogs:** Low revenue + low views → consider pausing or relisting with new copy/images

Use this 2×2 matrix mentally:
```
             High conversion   Low conversion
High views │    Stars (A)    │  Potential (B) │
Low views  │   Stable (C)   │    Dogs (D)    │
```

### 3. Identify root causes for B and D

**Tier B (high views, low conversion):**
- Price vs competitor? → run competitor-spy
- Main image weak? → run ai-hero-photo
- Description unclear? → run product-copy
- Wrong keywords drawing wrong buyers? → run etsy-listing-manager audit mode

**Tier D (low views, low conversion):**
- Not indexed? → SEO problem → rabbit listing skill
- Wrong category/tags? → listing audit
- No reviews? → retention skill for review request
- Seasonal? → trend-timer for relaunch timing

### 4. Revenue summary and ROAS bridge

If ad spend data is available:
```
Organic revenue = Total revenue - Ad-attributed revenue
Ad ROAS = Ad-attributed revenue / Ad spend
Blended ROAS = Total revenue / Total ad spend
```

Flag if Blended ROAS is below break-even (from campaign-plan).

### 5. Output

```
## 📊 Sales Review — [Platform] · [Period]

### revenue summary
Total revenue: $[X]
Total orders: [N]
Average order value: $[X]
Top category: [category]
Return rate: [%]

### product tiers

**Tier A — Stars**
| SKU | Revenue | Units | Conv% | Action |
|---|---|---|---|---|
| [name] | $X | N | X% | Restock + scale ads |

**Tier B — Potential**
| SKU | Revenue | Views | Conv% | Root cause | Fix |
|---|---|---|---|---|---|
| [name] | $X | N | X% | Weak main image | → ai-hero-photo |

**Tier C — Stable**
[List only, no action needed]

**Tier D — Dogs**
| SKU | Revenue | Views | Conv% | Recommendation |
|---|---|---|---|---|
| [name] | $X | N | X% | Pause + relist Q4 |

### roas bridge
Organic revenue: $[X]
Ad revenue: $[X] (ROAS: [X]×)
Blended ROAS: [X]× — [above / at / below break-even]

### top 3 actions this week
1. [Specific action → specific skill to use]
2. [Specific action → specific skill to use]
3. [Specific action → specific skill to use]
```

Report is complete when all products are tiered and top 3 actions name specific skills
or steps to execute.
