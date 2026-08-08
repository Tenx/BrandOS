---
name: amazon-listing
description: >
  Write Amazon-ready product listings: title, 5 bullet points, product description, backend
  search terms, and A+ content brief. Optionally publishes via Amazon SP-API if credentials
  are configured. Falls back to formatted copy for Seller Central manual paste if no credentials.
  Use when the user wants to create or optimize an Amazon listing.
  Triggers: "amazon listing", "亚马逊上架", "amazon发布", "亚马逊产品", "amazon title",
  "bullet points amazon", "backend keywords", "A+", "sp-api", "亚马逊".
---

# Amazon Listing

Write Amazon-compliant listing copy. With SP-API credentials: publishes directly.
Without credentials: outputs Seller Central paste-ready copy.

## Input

User provides:
- **Product copy** — paste from `product-copy` skill output, or describe the product
- **ASIN** (optional) — if updating an existing listing
- **Category / Browse node** — e.g. "Home & Kitchen > Candles", "Handmade > Home Décor"
- **Brand name** — registered in Amazon Brand Registry if applicable
- **Price + fulfillment** — FBA or FBM
- **Marketplace** — default `amazon.com`; also supports `.co.uk`, `.de`, `.co.jp`

## Amazon Copy Rules

Amazon has strict format requirements — follow exactly:

**Title** (≤200 chars, recommended ≤80 for mobile)
- Format: `[Brand] [Product Type] [Key Feature] – [Material/Size] – [Use Case/Occasion]`
- Capitalize first letter of each word (Title Case)
- No promotional phrases ("Best", "Sale", "#1")
- No special characters except hyphens and commas

**Bullet points** (5 bullets, ≤500 chars each, recommended ≤200)
- ALL CAPS lead word or phrase: `CLEAN BURN – ...`
- Benefit-first, feature as proof
- No pricing, availability, or seller information
- No subjective claims without evidence ("luxury", "best quality")

**Product description** (≤2000 chars)
- HTML allowed: `<b>`, `<br>`, `<ul>`, `<li>` only
- Expand on bullets with more detail and brand story
- End with brand positioning line

**Backend search terms** (≤250 bytes total, no commas, no repetition)
- Include synonyms, alternate spellings, Spanish terms if US market
- Do not repeat words already in title or bullets
- No competitor brand names

**A+ Content brief** (if Brand Registry enrolled)
- Module 1: Brand story (headline + 150-word paragraph + lifestyle image description)
- Module 2: Comparison chart (3–4 product variants or related SKUs)
- Module 3: Feature highlight (3 icons + short captions)

## Steps

### 1. Write all copy blocks

Follow Amazon copy rules above. Flag any content that risks policy violation.

### 2. Publish via SP-API (if credentials configured)

SP-API requires:
```bash
# ~/.amazon-listing/config.json
{
  "marketplace_id": "ATVPDKIKX0DER",
  "seller_id": "...",
  "lwa_app_id": "...",
  "lwa_client_secret": "...",
  "refresh_token": "..."
}
```

Get credentials: Seller Central → Apps & Services → Develop Apps → Add new app client
Authorization: Login with Amazon (LWA) OAuth flow

SP-API endpoint: `PUT /listings/2021-08-01/items/{sellerId}/{sku}`

**Note:** SP-API setup is complex. If credentials are not configured, output copy for
manual entry in Seller Central → Inventory → Add a Product.

### 3. Output

```
## 📦 Amazon Listing — [Product Name]

### title
[≤200 chars, Title Case]

### bullet points
• [LEAD WORD] – [benefit + feature proof]
• [LEAD WORD] – [benefit + feature proof]
• [LEAD WORD] – [benefit + feature proof]
• [LEAD WORD] – [benefit + feature proof]
• [LEAD WORD] – [benefit + feature proof]

### product description
[≤2000 chars, minimal HTML]

### backend search terms
[≤250 bytes, space-separated, no commas]

### a+ brief
Module 1 — Brand Story: [headline + paragraph + image description]
Module 2 — Comparison: [table outline]
Module 3 — Features: [3 × icon + caption]

### policy flags
[Any content that may violate Amazon guidelines — fix before submitting]

### api result
[ASIN/SKU if published, or "No SP-API credentials — paste into Seller Central manually"]
```

Report is complete when title, all 5 bullets, description, and backend search terms are
filled and policy flags section is checked.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "rabbit": {
    "amazon": {
      "asin": "string (if published)",
      "title": "string",
      "bullet_points": ["bullet1", "bullet2", "bullet3", "bullet4", "bullet5"],
      "backend_keywords": "string",
      "status": "draft | submitted"
    }
  }
}
```
