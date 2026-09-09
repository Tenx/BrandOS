# Brand Context Schema

Template for `~/.claude/projects/brand-os/<brand-name>/context.json`.

Copy this file, fill in `product` and `brand_dir`, then run skills in pipeline order.
Each skill appends its own section — never edit another module's fields.

```json
{
  "_meta": {
    "brand": "",
    "brand_dir": "~/.claude/projects/brand-os/<brand-name>/",
    "created": "YYYY-MM-DD",
    "pipeline_version": "2.0"
  },

  "product": {
    "keyword": "",
    "name": "",
    "category": "",
    "target_price_usd": 0,
    "ship_from": "China",
    "platforms": ["woocommerce"]
  },

  "hound": {
    "verdict": "",
    "winning_angle": "",
    "price_range": { "low": 0, "high": 0, "currency": "USD" },
    "buyer_pain_points": [],
    "top_keywords": [],
    "platform_signals": {
      "reddit": "",
      "instagram": "",
      "etsy": ""
    },
    "risks": "",
    "competitor": {
      "shop_name": "",
      "price_range": { "low": 0, "high": 0, "currency": "USD" },
      "what_they_do_well": [],
      "gaps": [],
      "visual_style": "",
      "their_keywords": [],
      "how_to_beat": ""
    },
    "trend": {
      "direction": "",
      "peak_months": [],
      "launch_window": "",
      "recommendation": ""
    }
  },

  "parrot": {
    "brand": {
      "name": "",
      "tagline": "",
      "short_bio": "",
      "long_bio": "",
      "voice": {
        "tone": "",
        "use_words": [],
        "avoid_words": []
      }
    },
    "copy": {
      "hook": "",
      "bullets": [],
      "story": "",
      "specs": ""
    },
    "hero_photos": {
      "method": "",
      "files": [],
      "collage": ""
    },
    "product_images": {
      "source_collage": "",
      "output_dir": "",
      "files": [],
      "count": 0
    }
  },

  "rabbit": {
    "woocommerce": {
      "product_id": "",
      "title": "",
      "status": "draft",
      "url": ""
    },
    "etsy": {
      "listing_id": "",
      "title": "",
      "tags": [],
      "status": "draft",
      "url": ""
    },
    "shopify": {
      "product_id": "",
      "handle": "",
      "title": "",
      "status": "draft",
      "url": ""
    },
    "amazon": {
      "asin": "",
      "title": "",
      "bullet_points": [],
      "backend_keywords": "",
      "status": "draft"
    },
    "ozon": {
      "product_id": "",
      "name_ru": "",
      "category_id": 0,
      "status": "draft"
    },
    "yun_delivery": {
      "orders_shipped": 0,
      "waybill_numbers": [],
      "carrier": "YunExpress",
      "shipped_at": ""
    }
  },

  "bee": {
    "audience": {
      "persona_summary": "",
      "platforms_ranked": [],
      "meta_interests": [],
      "tiktok_audiences": [],
      "pinterest_keywords": []
    },
    "creative": {
      "hero_image_brief": "",
      "video_hook": "",
      "copy_variants": []
    },
    "campaign": {
      "primary_platform": "",
      "break_even_roas": 0,
      "monthly_budget_usd": 0,
      "phases": [
        { "name": "cold start", "duration_days": 0, "budget_usd": 0, "goal": "" },
        { "name": "optimize",   "duration_days": 0, "budget_usd": 0, "goal": "" },
        { "name": "scale",      "duration_days": 0, "budget_usd": 0, "goal": "" }
      ],
      "kill_rules": []
    },
    "execution": {
      "kol": {
        "platform": "",
        "candidates": [],
        "messages_drafted": 0,
        "follow_up_cadence_days": [0, 3, 7]
      },
      "email": {
        "goal": "",
        "recipients": [],
        "sequence_days": [0, 3, 7],
        "drafts_created": 0,
        "sends_confirmed": 0
      },
      "ads": {
        "platforms": [],
        "scripts": [],
        "phase1_daily_budget_usd": 0,
        "break_even_roas": 0,
        "enabled_by_human": false
      }
    }
  },

  "elephant": {
    "sales_review": {
      "period": "",
      "total_revenue": 0,
      "total_orders": 0,
      "aov": 0,
      "blended_roas": 0,
      "tiers": { "A": [], "B": [], "C": [], "D": [] },
      "top_actions": []
    }
  },

  "results": {
    "_note": "MEASURED actuals only. Never written by skills. Plans live in bee.campaign.* and are never overwritten here.",
    "currency": "USD",
    "latest": {
      "period": "2026-08",
      "sales": {
        "orders": 0, "revenue": 0, "units_total": 0,
        "by_sku": [ { "sku_id": "", "units": 0, "revenue": 0 } ]
      },
      "funnel": { "sessions": 0, "conversion_rate": 0, "repeat_purchase_rate": 0, "aov": 0 },
      "ads": [ { "platform": "", "campaign_id": "", "spend": 0, "impressions": 0, "clicks": 0, "actual_roas": 0 } ]
    },
    "snapshots": [
      { "date": "YYYY-MM-DD", "metrics": { "revenue": 0, "orders": 0, "conversion_rate": 0, "blended_actual_roas": 0, "repeat_purchase_rate": 0 } }
    ]
  }
}
```

## Usage Notes

- Skills read only their own module's input fields (e.g. `hound` reads `product.keyword`)
- Skills write only their own module's output fields
- `_meta.pipeline_version` helps track schema changes across brands
- Store this file locally only — never commit to git (contains brand strategy)

## Plan vs Actual — the moat

The top-level `results` block is **MEASURED actuals only** and is physically separate from every planning field. This is the single most important design rule:

- **Plans** live in `bee.campaign.*` (break-even ROAS, target ROAS, budget phases) — written and overwritten by skills on every re-run.
- **Actuals** live in `results.*` — filled by a human (or a future importer), **never** by a skill.
- Because they are separate keys, re-running any skill (which only touches plan fields) can **never** overwrite real history. The record is append-only. This is the Klaviyo principle: the data layer only deepens, it never gets clobbered.

`results.latest` is a convenience snapshot (the current month, read fast). `results.snapshots[]` is an **append-only** time series — one `{date, metrics{}}` per period — so filtering the array shows the trend.

- Per-SKU actuals: `results.latest.sales.by_sku[].sku_id` aligns to `product.skus[].id` (or `parrot.copy.skus[].id` on older files).
- Per-platform ad actuals: `results.latest.ads[].platform` aligns to the planned `bee.campaign.platforms` — so plan vs actual joins directly.

## Canonical shapes (v2)

These are **declared, not enforced**. New files should follow one shape; the portfolio reader (`core/portfolio/aggregate.py`) tolerates the older/messier variants via its normalization layer.

- **phases** → array of `{name, duration_days, daily_budget_usd, platforms[], target_roas, goal, kill_rule}`
- **SKU pricing** → `product.skus[].price_usd` + `cogs_usd`; else brand-level `bee.campaign.price_usd` / `cogs_usd`
- **VI** → `parrot.vi`
- **bee.execution.ads** → `{platforms[], scripts[{platform,path,campaign_id}], enabled_by_human}`
- **COGS / break-even** → `bee.campaign.cogs_usd` + `bee.campaign.break_even_roas`

## Changelog

- **2.0** — Added top-level `results` block (measured actuals, append-only time series, plan/actual physically separated). Declared `## Canonical shapes (v2)` to converge new files without a forced migration. Older files (`brand`/`category` at top level, string prices, `parrot.copy.skus`) remain valid — the portfolio reader normalizes them.
- **1.0** — Initial per-module schema (product / hound / parrot / rabbit / bee / elephant).
