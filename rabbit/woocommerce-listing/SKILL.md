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

**Remove sidebar on all WooCommerce pages (correct method)**
`storefront_sidebar` is NOT a real action hook — do NOT use `remove_action('storefront_sidebar', ...)`.
The only reliable method is two filters together:
```php
add_filter('body_class', function ($classes) {
    $is_wc = function_exists('is_woocommerce') && (is_woocommerce() || is_cart() || is_checkout() || is_account_page());
    if ($is_wc || is_front_page()) {
        $classes[] = 'storefront-full-width-content';
    }
    return $classes;
});
add_filter('is_active_sidebar', function ($is_active, $index) {
    if ($index === 'sidebar-1') {
        $is_wc = function_exists('is_woocommerce') && (is_woocommerce() || is_cart() || is_checkout() || is_account_page());
        if ($is_wc || is_front_page()) return false;
    }
    return $is_active;
}, 10, 2);
```
`storefront-full-width-content` body class triggers Storefront's own full-width layout.
`is_active_sidebar` returning false prevents the sidebar widget area from rendering.
Both are required — one alone is insufficient.

**Replace WooCommerce product gallery (custom PHP gallery)**
WooCommerce's default gallery uses flexslider which fails on PHP built-in server (opacity:0,
images never visible). The correct approach is NOT `ob_start` stripping — instead, fully replace
the gallery action with a custom PHP renderer. This also gives full styling control:
```php
// In mu-plugin: remove WC gallery, add custom one
add_action('init', function () {
    remove_action('woocommerce_before_single_product_summary', 'woocommerce_show_product_images', 20);
});
add_action('woocommerce_before_single_product_summary', function () {
    global $product;
    if (!$product) return;
    $attachment_ids = $product->get_gallery_image_ids();
    $main_id        = $product->get_image_id();
    if (!$main_id) return;
    $main_src = wp_get_attachment_image_url($main_id, 'woocommerce_single');
    $main_alt = get_post_meta($main_id, '_wp_attachment_image_alt', true) ?: get_the_title();
    echo '<div class="woocommerce-product-gallery images">';  // keep class for Storefront float layout
    echo '<div class="brand-gallery">';
    echo '<div class="brand-gallery__main"><img id="brand-main-img" src="' . esc_url($main_src) . '" alt="' . esc_attr($main_alt) . '" /></div>';
    if (!empty($attachment_ids)) {
        echo '<div class="brand-gallery__thumbs">';
        echo '<img src="' . esc_url(wp_get_attachment_image_url($main_id, 'thumbnail')) . '" data-full="' . esc_url($main_src) . '" class="active" />';
        foreach ($attachment_ids as $id) {
            echo '<img src="' . esc_url(wp_get_attachment_image_url($id, 'thumbnail')) . '" data-full="' . esc_url(wp_get_attachment_image_url($id, 'woocommerce_single')) . '" />';
        }
        echo '</div>';
    }
    echo '</div></div>';
}, 20);
// Thumb click JS in wp_footer (only on single product)
add_action('wp_footer', function () {
    if (!is_singular('product')) return;
    echo '<script>document.addEventListener("DOMContentLoaded",function(){var m=document.getElementById("brand-main-img"),t=document.querySelectorAll(".brand-gallery__thumbs img");if(!m||!t.length)return;t.forEach(function(x){x.addEventListener("click",function(){m.src=x.dataset.full||x.src;t.forEach(function(y){y.classList.remove("active")});x.classList.add("active")})})});</script>';
});
```
IMPORTANT: wrap the gallery in `<div class="woocommerce-product-gallery images">` — Storefront
uses this class to apply `float:left; width:48%` for the two-column product layout.
Also suppress WC's own gallery CSS/JS output:
```css
.woocommerce-product-gallery .woocommerce-product-gallery__wrapper { display: none !important; }
.woocommerce-product-gallery .flex-control-nav,
.woocommerce-product-gallery .flex-direction-nav,
.woocommerce-product-gallery .woocommerce-product-gallery__trigger { display: none !important; }
```

**⚠️ Never use `sed` to edit PHP files with HTML attributes**
`sed` regex that matches across HTML attributes (e.g. `s/class="foo".*attr="bar"/...`) will
silently eat everything between the two matched attributes — including `src="..."` values.
Always use the Edit tool (exact string match + replace) when modifying PHP template lines.

**Custom brand homepage (editorial landing page) via shortcode**
Preferred method: register a `[brand_landing]` shortcode in the mu-plugin, create a WordPress
page, paste the shortcode, and set it as the static front page. Avoids page template file
management and works with any theme:
```php
// In mu-plugin
add_shortcode('brand_landing', function () {
    ob_start(); ?>
    <style>/* landing page styles */</style>
    <div class="lp-root"><!-- landing page HTML --></div>
    <?php return ob_get_clean();
});
```
Then set the page as static front page:
```bash
HOME_ID=$($WP post create --post_type=page --post_title="Home" --post_status=publish --post_content='[brand_landing]' --porcelain)
$WP option update show_on_front page
$WP option update page_on_front $HOME_ID
```

**Full-bleed landing page (break out of Storefront container)**
Storefront constrains `.entry-content` to a fixed column width. To make the shortcode full-viewport-width:
```css
/* 1. Hide Storefront's own header on the homepage */
.home .site-header { display: none !important; }

/* 2. Strip page scaffolding */
.home .entry-header, .home .page-header { display: none !important; }
.home .site-content { padding: 0 !important; margin: 0 !important; }
.home .site-content > .col-full { padding: 0 !important; max-width: 100% !important; width: 100% !important; }
.home .hentry { margin: 0 !important; }
.home .entry-content { padding: 0 !important; margin: 0 !important; }
.home .site-footer { display: none !important; }

/* 3. True full-viewport-width for the root element */
.home .lp-root {
  position: relative;
  left: 50%;
  margin-left: -50vw !important;
  width: 100vw !important;
  max-width: 100vw !important;
  overflow-x: hidden;
}
```
Build the landing page's own nav inside the shortcode HTML (sticky, z-index:100).
The full-bleed trick works because `.entry-content` has `overflow: visible` in Storefront.

**Brand VI design patterns (proven)**

*Dark Gallery VI* — for jewellery, art, luxury goods. Dark background makes product colours pop:
- Background: `#111111` / `#1c1c1c` surface
- Text: `#e8e2d9` warm off-white
- Accent: `#c9a84c` gold → `#e8c96a` hover
- Typography: Cormorant Garamond (serif, light weight) + Inter (sans, UI)
- Buttons: gold fill `#c9a84c`, square corner, uppercase 0.18em tracking
- Cards: no border, `opacity` hover transition, tight `2px` grid gaps

*Paper & Cutout VI* — for handmade, craft, artisan. Warm parchment, editorial stamp feel:
- Background: `#f5e6c8` parchment / `#fdf6e3` cream
- Ink: `#1a1a2e` deep navy
- Accents: `#d44444` red, `#1a4a8a` blue, `#f0c040` yellow
- Typography: Bebas Neue (display) + Space Mono (body)
- Buttons: yellow fill + `4px 4px 0 var(--red)` offset shadow, slight rotation

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
