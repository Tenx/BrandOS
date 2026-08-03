---
name: retention
description: >
  Build repeat purchase rate and customer lifetime value. Segments past buyers by behavior,
  generates re-engagement messages, bundle recommendations, and seasonal campaign briefs
  for Etsy, Shopify, and email.
  Use when the user wants to bring back past buyers, increase AOV, or run a seasonal push.
  Triggers: "复购", "老客户", "留存", "retention", "repeat purchase", "老买家",
  "bundle", "捆绑销售", "seasonal campaign", "节日营销", "email campaign", "老客回购".
---

# Retention

Turn one-time buyers into repeat customers. Segment → message → offer.

## Input

User provides:
- **Platform** — Etsy / Shopify / email list
- **Task** — one of:
  - `segment` — classify past buyers into tiers
  - `message` — draft re-engagement message for a segment
  - `bundle` — suggest product bundles to increase AOV
  - `campaign` — plan a seasonal or event-based push

If platform and task are missing, ask before proceeding.

## Steps

### Task: segment — classify past buyers

Pull order history and group buyers:

**Etsy:**
```bash
opencli browser main open "https://www.etsy.com/your/orders/completed"
opencli browser main extract
```

**Shopify (Admin API):**
```bash
GET /admin/api/2024-01/customers.json?fields=id,email,orders_count,total_spent,last_order_date
```

**Segments:**

| Segment | Criteria | Goal |
|---|---|---|
| **Champions** | 2+ orders, last order <60 days | Upsell, ask for referral |
| **Loyal** | 2+ orders, last order 60–180 days | Re-engage with new product |
| **Promising** | 1 order, last order <60 days | Convert to repeat with follow-up |
| **At risk** | 1 order, last order 60–180 days | Win back with offer |
| **Lost** | Any, last order >180 days | Low-effort reactivation or let go |

### Task: message — draft re-engagement

Write a message for a specific segment. Adapt tone to platform:

**Etsy Conversations** — personal, handmade seller warmth, no HTML
**Shopify email** — can use light formatting, subject line matters most
**Email list** — subject line A/B variants + preheader text

**Message structure:**
1. Subject/opener: reference the previous purchase specifically if possible
2. Body: one clear reason to come back (new product / seasonal relevance / exclusive offer)
3. CTA: single action (shop link, discount code, or new collection)
4. Length: 4–6 sentences max — do not over-explain

**Example — Promising segment (first-time buyer, 45 days ago):**
```
Subject: Something new you might like

Hi [name],

I hope you're still enjoying your [previous product]. I just added a few new scents
to the shop — including one that pairs really well with what you ordered.

[Link] — no pressure, just wanted to let you know.

[Shop name]
```

**Example — At risk segment (1 order, 90 days ago):**
```
Subject: It's been a while

Hi [name],

You ordered [product] back in [month] — hope it was everything you expected.
I've been adding new pieces and thought you might want to take a look.
Use [CODE10] for 10% off if you find something you like.

[Shop link]
```

### Task: bundle — suggest product bundles

Analyze current product catalog and order history to suggest natural bundles:

**Bundle logic:**
- **Frequency bundle:** products often bought together → offer as set at 10–15% discount
- **Tier bundle:** entry product + upgrade (e.g. single candle → candle + diffuser set)
- **Gifting bundle:** products that make sense as a curated gift box
- **Seasonal bundle:** products relevant to upcoming season/holiday

**Output:** 3 bundle suggestions with:
- Bundle name
- Products included
- Suggested price (vs. individual sum)
- Discount %
- Platform listing strategy (single listing with variants, or separate bundle listing)

### Task: campaign — seasonal push plan

Build a mini-campaign around a date or season:

**Key cross-border retail dates:**
| Date | Campaign | Lead time |
|---|---|---|
| Oct 31 | Halloween / Fall | 3 weeks before |
| Dec 1–25 | Holiday / Christmas gifting | 6 weeks before |
| Feb 14 | Valentine's Day | 3 weeks before |
| Mar 8 | International Women's Day | 2 weeks before |
| May (2nd Sun) | Mother's Day | 3 weeks before |
| Nov (4th Thu) | Thanksgiving / Black Friday | 4 weeks before |

**Campaign plan output (5 elements):**
1. **Hook** — seasonal angle for this product (not generic "holiday sale")
2. **Offer** — discount / bundle / free gift with purchase / limited edition
3. **Content calendar** — 3 social posts (dates + platform + brief from social-post skill)
4. **Email/message sequence** — 2 touches: teaser (1 week before) + launch day
5. **Listing updates** — seasonal keywords to add temporarily (feed to rabbit listing skills)

## Output

```
## 🔄 Retention — [Platform] · [Task]

### segments (if task=segment)
Champions: [N buyers] — [action]
Loyal: [N buyers] — [action]
Promising: [N buyers] — [action]
At risk: [N buyers] — [action]
Lost: [N buyers] — [action / skip]

### message draft (if task=message)
Segment: [segment name]
Platform: [etsy / shopify / email]
Subject: [subject line]
---
[message body]
---

### bundle suggestions (if task=bundle)
1. [Bundle name]: [products] · $[price] (save [%]) · [strategy]
2. ...
3. ...

### campaign plan (if task=campaign)
Event: [name + date]
Hook: [seasonal angle]
Offer: [specific offer]
Content:
  Post 1 [date]: [platform] — [brief]
  Post 2 [date]: [platform] — [brief]
  Post 3 [date]: [platform] — [brief]
Email sequence:
  Teaser [date]: [subject + 1-line brief]
  Launch [date]: [subject + 1-line brief]
Listing updates: [keywords to add → which skill to use]
```

Report is complete when the requested task section is filled and each item has
a specific next action or skill reference.
