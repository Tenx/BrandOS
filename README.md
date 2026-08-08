# BrandOS

AI-powered cross-border brand system for handmade & independent sellers.

## Modules

| Module | Animal | Focus |
|--------|--------|-------|
| ① Hound | 嗅探犬 | Product research & market validation |
| ② Parrot | 鹦鹉 | Brand story, content & visual identity |
| ③ Rabbit | 兔子 | Listing, SEO & publishing |
| ④ Bee | 蜜蜂 | Paid traffic & distribution |
| ⑤ Elephant | 大象 | Data review, fulfillment & retention |

## Skills

### Hound (① 嗅探犬) — Product research & market validation
- [`hound/market-scout`](hound/market-scout) — Scout a category across Reddit + Instagram + Etsy → decision-ready report
- [`hound/competitor-spy`](hound/competitor-spy) — Deep-dive a competitor shop → gaps, weaknesses, how to beat them
- [`hound/trend-timer`](hound/trend-timer) — Detect seasonality and timing signals → when to launch

### Parrot (② 鹦鹉) — Brand story, content & visual identity
- [`parrot/brand-story`](parrot/brand-story) — Brand name, tagline, about/bio text & voice guide → paste-ready for any platform
- [`parrot/product-copy`](parrot/product-copy) — Product hook, bullets, story & specs → platform-neutral copy for Rabbit skills
- [`parrot/social-post`](parrot/social-post) — Instagram, Pinterest, TikTok & Facebook posts from one product brief
- [`parrot/ai-hero-photo`](parrot/ai-hero-photo) — AI hero image generation: model ref + garment flatlay → 4-view product photos
- [`parrot/product-collage-outpaint`](parrot/product-collage-outpaint) — Post-process hero images: split collage, upscale, FLUX background extension

### Rabbit (③ 兔子) — Listing, SEO & publishing
- [`rabbit/etsy-listing-manager`](rabbit/etsy-listing-manager) — Etsy listing SEO copy, titles, tags, attributes, CSV audit, draft publishing & OAuth
- [`rabbit/shopify-listing`](rabbit/shopify-listing) — Shopify product listing: title, body HTML, SEO meta, tags + Admin API publish
- [`rabbit/woocommerce-listing`](rabbit/woocommerce-listing) — WooCommerce product listing: name, description, Yoast SEO, attributes + REST API publish
- [`rabbit/amazon-listing`](rabbit/amazon-listing) — Amazon listing: title, bullets, description, backend keywords, A+ brief + SP-API publish
- [`rabbit/ozon-listing`](rabbit/ozon-listing) — Ozon listing: Russian copy, attributes, rich content + Seller API publish
- [`rabbit/yun-delivery`](rabbit/yun-delivery) — Cross-border fulfillment via YunExpress (云途): submit waybills, process Etsy orders

### Bee (④ 蜜蜂) — Paid traffic & distribution
- [`bee/audience-finder`](bee/audience-finder) — Build buyer persona + platform targeting parameters for Meta, Pinterest, TikTok, Google Shopping
- [`bee/ad-creative-brief`](bee/ad-creative-brief) — Generate image specs, video hooks, A/B copy variants per platform from product copy
- [`bee/campaign-plan`](bee/campaign-plan) — ROAS-driven 3-phase campaign plan: budget allocation, bid strategy, kill rules, scale rules

### Elephant (⑤ 大象) — Data review, fulfillment & retention
- [`elephant/customer-service`](elephant/customer-service) — Cross-platform buyer messaging: Etsy, Amazon, Shopify — read, classify, draft, send
- [`elephant/sales-review`](elephant/sales-review) — Weekly/monthly sales analysis: tier products by performance, identify root causes, output top 3 actions
- [`elephant/review-manager`](elephant/review-manager) — Monitor reviews, reply to negatives, request reviews from satisfied buyers
- [`elephant/retention`](elephant/retention) — Segment past buyers, draft re-engagement messages, suggest bundles, plan seasonal campaigns

## 9.9 Intro Guide
¥9.9 跨境实战资料包 — Parrot 模块配套入门教程，主图改造 + Brand OS 系统导览

## Workflow Docs

Reference docs for recurring operational tasks (not skills — these are process guides):

| File | Purpose |
|------|---------|
| [`pipeline.md`](pipeline.md) | **Full pipeline entry point** — step-by-step from market research to live listing, with context.json handoffs |
| [`context-schema.md`](context-schema.md) | **Brand context.json template** — persistent state file shared across all skills in a pipeline run |
| [`lark-delivery.md`](lark-delivery.md) | Feishu client delivery — folder structure, upload, docs creation, public link permissions |
| [`pdf-report.md`](pdf-report.md) | HTML→PDF via Puppeteer + Replicate gpt-image-2 hero photo generation |

## Chain Guide

Full pipeline from zero to live:

```
Hound/market-scout       ← pick category
      ↓ (winning angle + pain points + price)
Parrot/brand-story       ← brand name, tagline, voice
Parrot/product-copy      ← hook, bullets, story, specs
      ↓
Rabbit/*-listing         ← publish to WooCommerce / Etsy / Shopify / Amazon / Ozon
Parrot/ai-hero-photo     ← product images (apparel: dual-input; other: Replicate direct)
      ↓
Bee/audience-finder      ← buyer persona + platform targeting
Bee/ad-creative-brief    ← image/video brief + copy variants
Bee/campaign-plan        ← 3-phase plan with ROAS targets
      ↓
Elephant/sales-review    ← weekly review → identify issues → fix with relevant skill
Elephant/review-manager  ← monitor + respond to reviews
Elephant/retention       ← re-engage past buyers
```
