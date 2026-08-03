---
name: woocommerce-listing
description: >
  Write and publish product listings to WooCommerce (WordPress). Generates SEO title, description,
  short description, attributes, tags, and categories — then publishes via WooCommerce REST API
  if credentials are configured. Falls back to formatted copy for manual paste if no credentials.
  Use when the user wants to add or update a product on their WooCommerce store.
  Triggers: "woocommerce", "wordpress上架", "woo listing", "发布到woo", "wordpress产品",
  "woocommerce publish", "add product woocommerce", "独立站woo".
---

# WooCommerce Listing

Write and publish one product to WooCommerce. With API credentials: creates draft via REST API.
Without credentials: outputs paste-ready formatted copy.

## Input

User provides:
- **Product copy** — paste from `product-copy` skill output, or describe the product
- **Store URL** — e.g. `https://mystore.com`
- **Category** (optional) — which WooCommerce category to assign
- **Price** — regular price; sale price optional
- **Attributes** (optional) — e.g. Size: S/M/L, Color: Black/White

First-time setup: ask for API credentials if not configured (see Setup below).

## Setup (one-time)

```bash
# Store credentials in ~/.woocommerce-listing/config.json
# Never write keys into code or SKILL.md
{
  "url": "https://mystore.com",
  "consumer_key": "ck_xxxxxxxxxxxx",
  "consumer_secret": "cs_xxxxxxxxxxxx"
}
```

Get keys: WordPress Admin → WooCommerce → Settings → Advanced → REST API → Add key
Permissions: Read/Write

## Steps

### 1. Write listing copy

**Product name** (≤70 chars)
- Keyword-first, natural language
- No ALL CAPS, no punctuation spam

**Short description** (≤160 chars)
- Shown on shop/category pages
- Hook sentence from product-copy, benefit-led

**Full description**
- Opening paragraph: story/hook (60–80 words)
- `<h3>Features</h3>` + `<ul>` with 5 bullets
- `<h3>Details</h3>` + specs as `<ul>`
- Clean HTML, no inline styles

**Yoast / SEO meta** (if Yoast SEO plugin active)
- Focus keyphrase: primary search term
- SEO title (≤60 chars)
- Meta description (≤160 chars)

**Tags** — 8–12: product type, material, style, use case

**Attributes** — map user-provided variants to WooCommerce attribute format

### 2. Publish via API (if credentials configured)

```
POST /wp-json/wc/v3/products
```

Payload:
```json
{
  "name": "...",
  "type": "simple",
  "status": "draft",
  "description": "...",
  "short_description": "...",
  "regular_price": "...",
  "categories": [{ "name": "..." }],
  "tags": [{ "name": "..." }],
  "attributes": [{ "name": "Size", "options": ["S","M","L"], "visible": true }]
}
```

Always create as `"status": "draft"` first. Confirm with user before publishing.

For variable products (multiple variants), use `"type": "variable"` and create variations
via `POST /wp-json/wc/v3/products/{id}/variations` after the parent product is created.

### 3. Output

```
## 🔌 WooCommerce Listing — [Product Name]

### product name
[≤70 chars]

### short description
[≤160 chars]

### full description
[formatted HTML]

### seo (Yoast)
Focus keyphrase: [primary term]
SEO title: [≤60 chars]
Meta description: [≤160 chars]

### tags
[comma-separated list]

### attributes
[Name: option1 / option2 / option3]

### api result
[Draft product ID and admin URL if published, or "No credentials — paste copy manually"]
```

Report is complete when name, short description, and full description are filled.
If credentials exist, report is complete only after draft product URL is confirmed.
