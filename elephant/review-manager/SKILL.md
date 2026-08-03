---
name: review-manager
description: >
  Monitor, respond to, and proactively grow product reviews across Etsy, Amazon, and Shopify.
  Detects new reviews via browser, classifies sentiment, drafts public replies to negative reviews,
  and generates review request messages for happy buyers.
  Use when the user wants to protect their rating, respond to a bad review, or get more reviews.
  Triggers: "评价", "差评", "好评", "review", "评论", "催评", "reply to review",
  "bad review", "negative review", "review request", "ask for review", "星级".
---

# Review Manager

Monitor reviews → respond to negatives → request reviews from satisfied buyers.
Works across Etsy, Amazon, and Shopify.

## Input

User provides:
- **Platform** — Etsy / Amazon / Shopify
- **Task** — one of:
  - `monitor` — check for new reviews since last session
  - `reply` — draft a public reply to a specific review
  - `request` — send review request to recent buyers

If platform is missing, ask before proceeding.

## Steps

### Task: monitor — check new reviews

**Etsy:**
```bash
opencli browser main open "https://www.etsy.com/your/reviews"
opencli browser main extract
```

**Amazon:**
```bash
opencli browser main open "https://sellercentral.amazon.com/product-reviews"
opencli browser main extract
```

**Shopify:**
```bash
# If using Judge.me, Loox, or Stamped.io:
opencli browser main open "https://<shop>.myshopify.com/admin/apps/<review-app>"
opencli browser main extract
```

Extract: star rating, review text, buyer name, product, date.
Classify: 5★ (positive) / 4★ (neutral) / 1–3★ (negative → urgent).

### Task: reply — respond to a review

**Reply rules:**
- Only reply to 1–3★ reviews (public replies on negatives protect brand perception)
- Never reply to positive reviews on Amazon (Amazon policy violation risk)
- Etsy: can reply to any review; keep positive reply replies brief and warm

**Negative review reply framework:**
1. **Acknowledge** — validate the frustration without full blame admission
2. **Apologize** — short and genuine
3. **Resolve** — what you did or will do (replacement, refund, explanation)
4. **Invite offline** — "Please reach out directly so I can make this right"
5. **Never:** argue, make excuses, attack the buyer, paste a template verbatim

**Tone by platform:**
- Etsy: warm and personal — other shoppers are reading this
- Amazon: professional and brief — max 3 sentences; Amazon buyers scan fast

**Example framework (adapt to brand voice):**
> I'm sorry this wasn't the experience you expected — [specific issue acknowledged]. I've already [action taken / reached out]. Please message me directly so I can make it right. — [Shop name]

### Task: request — ask satisfied buyers for a review

**Timing rules:**
- Etsy: send after delivery confirmation + 3 days (Etsy auto-reminder handles some of this)
- Amazon: use "Request a Review" button in Seller Central — compliant, no custom message allowed
- Shopify: send 7–10 days after estimated delivery

**Identify candidates:**
```bash
# Etsy — completed orders in last 14 days with no review yet
opencli browser main open "https://www.etsy.com/your/orders/completed"
opencli browser main extract
```

Filter: orders delivered >3 days ago, no review submitted, no prior complaint.

**Review request message (Etsy / Shopify):**

```
Subject: How did your [product name] arrive?

Hi [name],

I hope your [product] arrived safely and you love it. If you have a moment,
leaving a review really helps small shops like mine reach more people who'd
appreciate it.

[Etsy review link] or [Shopify review link]

Either way — thank you for your order. 🙏

[Shop name]
```

Keep it short. One ask. No pressure language ("please please", "it would mean the world").

**Amazon review request:**
```bash
# Navigate to order in Seller Central → click "Request a Review"
# Amazon sends a standardized compliant message — do not send custom messages
opencli browser main open "https://sellercentral.amazon.com/orders-v3"
opencli browser main find --role button --text "Request a Review"
opencli browser main click <ref>
```

## Review Escalation Rules

| Situation | Action |
|---|---|
| 1★ with photo evidence of damage | Offer full replacement immediately, no questions |
| 1★ mentioning "not as described" | Check listing copy → flag for product-copy fix |
| 1★ from buyer who never contacted you | Reply publicly + invite direct contact; do not refund publicly |
| Multiple 1★ same complaint | Systemic issue → fix product or listing, not just reply |
| Fake/malicious review | Report to platform; do not reply aggressively |

## Output

```
## ⭐ Review Manager — [Platform]

### new reviews
[Date] · [★★★★★] · [buyer] · [product]: "[excerpt]" → [action: reply / request / none]

### draft reply (if negative)
Platform: [platform]
Review: "[original text]"
Draft:
"[reply in brand voice, ≤3 sentences for Amazon, ≤5 for Etsy]"

### review request candidates
[buyer name] · [product] · delivered [date] · [send / skip]

### draft request message
[message text]

### flags
[Any systemic issues detected across multiple reviews]
```

Workflow is complete when all new reviews are classified, negative replies are drafted,
and review request candidates are identified with send/skip decision.
