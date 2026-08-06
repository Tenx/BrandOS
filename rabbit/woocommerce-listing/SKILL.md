---
name: woocommerce-listing
description: >
  Write and publish product listings to WooCommerce (WordPress). Generates SEO title, description,
  short description, attributes, tags, and categories — then publishes via WP-CLI (local) or
  WooCommerce REST API (remote). Falls back to formatted copy for manual paste if neither is available.
  Use when the user wants to add or update a product on their WooCommerce store.
  Triggers: "woocommerce", "wordpress上架", "woo listing", "发布到woo", "wordpress产品",
  "woocommerce publish", "add product woocommerce", "独立站woo".
---

# WooCommerce Listing

Write and publish one product to WooCommerce. Two publish paths:
- **WP-CLI** (preferred for local/SSH installs) — no REST API credentials needed
- **REST API** (for remote stores with API keys)
- **No credentials** — outputs paste-ready formatted copy

## Input

User provides:
- **Product copy** — paste from `product-copy` skill output, or describe the product
- **Store path or URL** — local path (e.g. `/var/www/mystore`) or `https://mystore.com`
- **Category** (optional) — which WooCommerce category to assign
- **Price** — regular price; sale price optional
- **Attributes** (optional) — e.g. Size: S/M/L, Color: Black/White

## Setup (one-time, REST API path only)

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

### 2a. Publish via WP-CLI (local installs)

**IMPORTANT**: Always use `-d memory_limit=512M` and `-d error_reporting=E_ALL\&~E_DEPRECATED`.
Default PHP memory (128MB) will fail on WooCommerce. PHP 8.5+ throws many deprecation notices
that break WP-CLI output parsing if not suppressed.

```bash
WP="php -d memory_limit=512M -d error_reporting=E_ALL&~E_DEPRECATED /opt/homebrew/bin/wp --path=/path/to/wordpress"

# Step 1: create product (returns product ID)
$WP wc product create \
  --user=admin \
  --name="Product Name" \
  --type=simple \
  --status=draft \
  --regular_price="65.00" \
  --short_description="Short desc here" \
  --porcelain

# Step 2: update full description and tags (use product ID from step 1)
PRODUCT_ID=<id from step 1>
$WP wc product update $PRODUCT_ID \
  --user=admin \
  --description="<p>Full HTML description...</p>" \
  --tags='[{"name":"tag1"},{"name":"tag2"}]'

# Step 3: Yoast SEO meta (if Yoast plugin installed)
$WP post meta update $PRODUCT_ID _yoast_wpseo_focuskw "focus keyphrase"
$WP post meta update $PRODUCT_ID _yoast_wpseo_title "SEO Title ≤60 chars"
$WP post meta update $PRODUCT_ID _yoast_wpseo_metadesc "Meta description ≤160 chars"
```

**Why two steps (create + update)?**
`wc product create` has a character limit that causes silent truncation on long `--description`.
Always write the full description via `wc product update` after creation.

**Preview (local PHP built-in server)**
PHP built-in server does NOT support `.htaccess` rewrites. Use plain query-string URLs:
```bash
# Start server with router
php -d memory_limit=512M -S localhost:8080 -t /path/to/wordpress /path/to/wordpress/router.php

# router.php content:
# <?php
# $uri = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
# if ($uri !== '/' && file_exists(__DIR__ . $uri)) { return false; }
# $_SERVER['SCRIPT_FILENAME'] = __DIR__ . '/index.php';
# include __DIR__ . '/index.php';

# Access product via query param (NOT pretty permalink)
open "http://localhost:8080/?p=<product_id>"
```

Do NOT set permalink structure to `/%postname%/` on a PHP built-in server — pretty permalinks
require `.htaccess` which the built-in server ignores. Keep permalink structure as plain (`''`)
or use `?p=ID` query param to preview.

WooCommerce will redirect `?p=<id>` to `?product=<slug>` automatically — follow the redirect,
do not fight it. The actual working URL is `?product=<slug>`.

**Theme choice matters for local preview**
Block themes (Twenty Twenty-Four, Twenty Twenty-Five) do NOT render WooCommerce product images
correctly on PHP built-in server — CSS/JS assets fail to load. Install Storefront (WooCommerce's
official theme) for correct product page rendering:
```bash
$WP theme install storefront --activate
```
Even with Storefront, the product gallery image may appear blank locally because WooCommerce's
flexslider JS requires full asset pipeline. The image IS attached correctly (verify with
`wc product get <id> --fields=images`). On a real Nginx/Apache server it renders fine.

**Upload product images via WP-CLI**
```bash
# Step 1: import image to media library and attach to product
ATTACH_ID=$($WP media import /path/to/hero.png \
  --title="product-hero" \
  --post_id=$PRODUCT_ID \
  --porcelain)

# Step 2: set as WooCommerce featured image (use wc product update, NOT post meta)
$WP wc product update $PRODUCT_ID --user=admin \
  --images="[{\"id\":$ATTACH_ID}]"

# Step 3: regenerate thumbnails (required for WooCommerce to show image)
$WP media regenerate --yes
```

Note: setting `_thumbnail_id` post meta directly does NOT work with WooCommerce block themes.
Always use `wc product update --images` to set the product image.

### 2b. Publish via REST API (remote stores)

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

### publish result
[Draft product ID and admin URL if published via WP-CLI or API, or "No credentials — paste copy manually"]
```

Report is complete when name, short description, and full description are filled.
If credentials / WP-CLI available, report is complete only after draft product ID is confirmed.
