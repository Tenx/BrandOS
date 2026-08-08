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
    "pipeline_version": "1.0"
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
  }
}
```

## Usage Notes

- Skills read only their own module's input fields (e.g. `hound` reads `product.keyword`)
- Skills write only their own module's output fields
- `_meta.pipeline_version` helps track schema changes across brands
- Store this file locally only — never commit to git (contains brand strategy)
