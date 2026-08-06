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

**Fix flexslider blank image on PHP built-in server**
WooCommerce's flexslider JS initializes but fails silently, positioning slides at `left:-99999px`.
`wp_dequeue_script` does NOT work — WooCommerce registers scripts via its own internal loader.
Only reliable fix is output buffering to strip the script tag from final HTML:
```php
# wp-content/mu-plugins/sacredthreads-brand.php (or any mu-plugin)
add_action('template_redirect', function() {
    if (!is_singular('product')) return;
    ob_start(function($html) {
        $html = preg_replace('/<script[^>]+id="wc-flexslider-js"[^>]*>.*?<\/script>/is', '', $html);
        $html = preg_replace('/<script[^>]+id="wc-single-product-js"[^>]*>.*?<\/script>/is', '', $html);
        return $html;
    });
});
```
Without flexslider JS, WooCommerce gallery falls back to plain HTML — image displays naturally.
Also add JS fallback in `wp_footer` to force `position:static` on gallery images in case other
JS runs after the ob_start strip.

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

**WooCommerce "Coming Soon" mode — check first**
New WooCommerce installs default to `woocommerce_coming_soon = yes`, which renders a blank
white page for ALL store pages (shop, product, cart). Check and disable before debugging
anything else:
```bash
$WP option get woocommerce_coming_soon        # should be "no"
$WP option update woocommerce_coming_soon no  # disable if yes
```

**Block Cart/Checkout/My Account — replace with classic shortcodes**
WooCommerce 8+ defaults to Gutenberg Block versions of Cart, Checkout, and My Account.
These depend on React + REST API + AJAX and do NOT work on PHP built-in server.
Replace page content with classic shortcodes:
```bash
$WP post update <cart_page_id>       --post_content='[woocommerce_cart]'
$WP post update <checkout_page_id>   --post_content='[woocommerce_checkout]'
$WP post update <myaccount_page_id>  --post_content='[woocommerce_my_account]'

# Get page IDs:
$WP option get woocommerce_cart_page_id
$WP option get woocommerce_checkout_page_id
$WP option get woocommerce_myaccount_page_id
```
Classic shortcodes render server-side and work on PHP built-in server without REST API.

**Enable redirect to cart after Add to Cart**
By default WooCommerce stays on the product page after adding to cart (AJAX add).
AJAX also fails on PHP built-in server. Enable redirect:
```bash
$WP option update woocommerce_cart_redirect_after_add yes
```

**Apply brand styles via must-use plugin**
To override Storefront's default styling globally (all pages: shop, product, cart, checkout,
my account, footer), use a must-use plugin instead of child theme or Customizer — it loads
automatically and survives theme updates:
```
wp-content/mu-plugins/brand.php
```
Use `add_action('wp_head', function() { ?><style>...</style><?php }, 99)` to inject CSS after
all theme stylesheets. Target body classes for page-specific overrides:
- `body.single-product` — product detail pages
- `body.woocommerce-cart` — cart page
- `body.woocommerce-checkout` — checkout page
- `body.woocommerce-account` — my account
- `body.tax-product_cat`, `body.post-type-archive-product` — shop/archive

Key CSS targets for Storefront brand override:
```css
.site-header .site-title a   /* brand name */
.main-navigation ul li a     /* nav links */
.site-header-cart a          /* cart link in header */
.woocommerce ul.products li.product .woocommerce-loop-product__title  /* shop card title */
button.single_add_to_cart_button  /* product page CTA */
#place_order                 /* checkout submit */
.woocommerce-MyAccount-navigation ul li a  /* account sidebar */
```

**Custom brand homepage (editorial landing page)**
To replace the default WooCommerce shop homepage with a full custom brand landing page:
1. Create a Storefront page template: `wp-content/themes/storefront/page-<slug>.php`
   - Output custom HTML/CSS inside WordPress's `wp_head()` / `wp_footer()` wrapper
   - Use `get_permalink($product_id)` and `wp_get_attachment_url($attach_id)` for dynamic URLs
   - Use `home_url('/?add-to-cart=ID')` for cart links — WooCommerce session works normally
2. Create a WordPress page with slug matching the template filename:
   ```bash
   HOME_ID=$($WP post create --post_type=page --post_title="Home" --post_name="<slug>" --post_status=publish --porcelain)
   $WP option update show_on_front page
   $WP option update page_on_front $HOME_ID
   ```
3. Hide Storefront's default header/footer on this page via CSS body class targeting.

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
