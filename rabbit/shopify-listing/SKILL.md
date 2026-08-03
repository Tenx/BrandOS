---
name: shopify-listing
description: >
  Write and publish product listings to Shopify. Generates SEO-optimized title, body HTML,
  metafields, tags, and collections — then publishes via Shopify Admin API if a token is
  configured. Falls back to formatted copy output for manual paste if no token.
  Use when the user wants to add or update a product on their Shopify store.
  Triggers: "shopify", "独立站上架", "shopify listing", "发布到shopify", "shopify产品",
  "shopify publish", "add product shopify".
---

# Shopify Listing

Write and publish one product to Shopify. With API token: creates draft product via Admin API.
Without token: outputs paste-ready formatted copy.

## Input

User provides:
- **Product copy** — paste from `product-copy` skill output, or describe the product
- **Store URL** — e.g. `myshop.myshopify.com`
- **Collection** (optional) — which collection to add it to
- **Price** — in store currency
- **Variants** (optional) — size, color, or other options with individual prices/SKUs

First-time setup: ask for API token if not configured (see Setup below).

## Setup (one-time)

```bash
# Store credentials in ~/.shopify-listing/config.json
# Never write tokens into code or SKILL.md
{
  "shop": "myshop.myshopify.com",
  "access_token": "shpat_xxxxxxxxxxxx"
}
```

Get a token: Shopify Admin → Apps → Develop apps → Create app → Admin API scopes:
`write_products`, `read_products`, `write_inventory`

## Steps

### 1. Write listing copy

**Title** (≤70 chars)
- Format: `[Product Type] | [Key Feature] | [Brand or Material]`
- Front-load the most searchable term
- No ALL CAPS, no keyword stuffing

**Body HTML**
- Opening paragraph: story/hook from product-copy (60–80 words)
- Features list: `<ul>` with 5 bullets (feature — benefit format)
- Care/specs section: `<p><strong>Details</strong></p>` + `<ul>`
- No inline styles; keep HTML clean for theme compatibility

**SEO meta title** (≤60 chars) — keyword-first, different from product title
**SEO meta description** (≤160 chars) — benefit-led, ends with soft CTA

**Tags** — 8–12 comma-separated: product type, material, style, occasion, use case

**Collections** — map to existing store collections or suggest new one

### 2. Publish via API (if token configured)

```
POST /admin/api/2024-01/products.json
```

Payload:
```json
{
  "product": {
    "title": "...",
    "body_html": "...",
    "vendor": "<brand name>",
    "product_type": "...",
    "tags": "...",
    "status": "draft",
    "variants": [{ "price": "...", "sku": "..." }],
    "metafields": [
      { "namespace": "seo", "key": "title", "value": "...", "type": "single_line_text_field" },
      { "namespace": "seo", "key": "description", "value": "...", "type": "single_line_text_field" }
    ]
  }
}
```

Always create as `"status": "draft"` first. Confirm with user before setting `"status": "active"`.

### 3. Output

```
## 🛍 Shopify Listing — [Product Name]

### title
[≤70 chars]

### body_html
[formatted HTML]

### seo
Meta title: [≤60 chars]
Meta description: [≤160 chars]

### tags
[comma-separated list]

### collection
[collection name or suggestion]

### api result
[Draft product ID and admin URL if published, or "No token — paste copy manually"]
```

Report is complete when title, body_html, and SEO fields are filled. If API token exists,
report is complete only after draft product URL is confirmed.
