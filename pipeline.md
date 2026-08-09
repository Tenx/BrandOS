# BrandOS Pipeline

Single entry point for running the full brand pipeline. Each step reads from and writes
to the brand's `context.json` file — no copy-pasting between skills.

## Setup

For each new brand, create a context file first:

```bash
BRAND=my-brand   # e.g. sumeru, shenbox
mkdir -p ~/.claude/projects/brand-os/$BRAND
cp context-schema.md ~/.claude/projects/brand-os/$BRAND/context.json
# Edit context.json: fill in "product" and "brand_dir" at minimum
```

## Full Pipeline

Run steps in order. Each step is optional — skip if already done.

---

### Step 1 — Market Validation (Hound)

**Skill**: `hound/market-scout`
**Input from context.json**: `product.keyword`
**Output to context.json**: `hound.*`

```
Trigger: "用brand-os做一下 [品类关键词]"
```

Optional:
- `hound/competitor-spy` → adds `hound.competitor.*`
- `hound/trend-timer` → adds `hound.trend.*`

**Handoff to Step 2**: paste into next prompt:
```
Winning angle: [hound.winning_angle]
Buyer pain points: [hound.buyer_pain_points top 2–3]
Price point: [hound.price_range.low]–[hound.price_range.high] USD
```

---

### Step 2 — Brand Identity (Parrot)

**Skill**: `parrot/brand-story`
**Input from context.json**: `hound.winning_angle`, `hound.buyer_pain_points`, `product.*`
**Output to context.json**: `parrot.brand.*`

Then:

**Skill**: `parrot/product-copy`
**Input from context.json**: `parrot.brand.voice`, `product.*`
**Output to context.json**: `parrot.copy.*`

---

### Step 3 — Hero Images (Parrot)

**Apparel products**: `parrot/ai-hero-photo` (dual-input: model ref + garment)
**All other products**: Replicate direct — see `pdf-report.md` → Hero Photo Generation

**Output to context.json**: `parrot.hero_photos.*`

---

### Step 4 — Listing & Publish (Rabbit)

Choose platform:

| Platform | Skill | Best for |
|----------|-------|---------|
| **Snipcart + static HTML** | manual (no skill yet) | Client demos, fast deploys, Vercel |
| WooCommerce | `rabbit/woocommerce-listing` | Clients who need WordPress |
| Etsy | `rabbit/etsy-listing-manager` | Marketplace |
| Shopify | `rabbit/shopify-listing` | Scaling DTC |
| Amazon | `rabbit/amazon-listing` | Marketplace |
| Ozon | `rabbit/ozon-listing` | Russia market |

> **Default for new client demos**: Snipcart + static HTML → deploy Vercel.
> WooCommerce local demo has too many rough edges; reserve for clients who specifically need WP.

**Input from context.json**: `parrot.copy.*`, `parrot.hero_photos.files`
**Output to context.json**: `rabbit.[platform].*`

---

### Step 5 — Paid Traffic (Bee)

Run in sequence:

1. `bee/audience-finder` → `context.json: bee.audience.*`
2. `bee/ad-creative-brief` → `context.json: bee.creative.*`
3. `bee/campaign-plan` → `context.json: bee.campaign.*`

**Input**: `parrot.copy.*`, `rabbit.[platform].*`, `hound.price_range`
**Key output**: `bee.campaign.break_even_roas`, `bee.campaign.phases`

---

### Step 6 — Ongoing (Elephant)

Run weekly/monthly:

| Task | Skill | Trigger |
|------|-------|---------|
| Sales analysis | `elephant/sales-review` | Weekly |
| Review monitoring | `elephant/review-manager` | Daily |
| Customer service | `elephant/customer-service` | As needed |
| Re-engagement | `elephant/retention` | Monthly |

`elephant/sales-review` output (`top_actions`) feeds back into the relevant skill for fixes.

---

## Client Delivery

After Steps 1–4, deliver to client via Feishu:

```bash
# See lark-delivery.md for full workflow
lark-cli drive +create-folder --name "<Brand> · <产品名>" --folder-token <客户交付_token>
# Upload PDFs, set permissions (two-step: tenant_readable → anyone_readable)
```

## Context File Location

```
~/.claude/projects/brand-os/<brand-name>/context.json
```

Each skill reads the fields it needs and appends/updates its own section.
Skills should never overwrite fields from other modules.
