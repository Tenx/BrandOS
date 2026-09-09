#!/usr/bin/env python3
"""Brand OS — portfolio aggregator (read-only).

Scans every customers/*/context.json, normalizes the messy real-world
shapes into a common per-brand row, buckets by category, and emits
cross-portfolio benchmarks + a plan-vs-actual table.

Design rules:
  - stdlib only (json / glob / statistics / pathlib)
  - NEVER crashes: every file is loaded under try/except; bad files land
    in `skipped[]` with a reason. Missing bee/product/elephant, bare-string
    prices, `elephant: {}` — all tolerated.
  - read-only: reads context.json, writes benchmarks.json + prints markdown.
    Touches nothing else.
  - path handling is cwd-independent: project root is derived from this
    file's location, never hardcoded.

This is the moat layer. ChatGPT can write copy for one new brand; it cannot
produce YOUR proprietary cross-portfolio truth ("incense runs ~$28 median,
break-even ~2.2x"), because it never sees the accumulated results.
"""

import glob
import json
import statistics
from pathlib import Path

# core/portfolio/aggregate.py -> core/portfolio -> core -> <project root>
BASE = Path(__file__).resolve().parents[2]
CUSTOMERS_GLOB = str(BASE / "customers" / "*" / "context.json")
OUT_PATH = Path(__file__).resolve().parent / "benchmarks.json"

# free-text category -> canonical bucket
CATEGORY_MAP = [
    ("incense", "incense"),
    ("fragrance", "incense"),
    ("tea", "tea"),
    ("beverage", "tea"),
    ("jewel", "jewelry"),
    ("charm", "spiritual"),
    ("scroll", "spiritual"),
    ("deity", "spiritual"),
    ("spiritual", "spiritual"),
    ("blessing", "spiritual"),
    ("apparel", "apparel"),
    ("knit", "apparel"),
    ("crochet", "apparel"),
    ("sweater", "apparel"),
    ("pet", "pet"),
    ("dog", "pet"),
    ("harness", "pet"),
    ("leash", "pet"),
    ("cushion", "homeware"),
    ("pillow", "homeware"),
    ("textile", "homeware"),
    ("homeware", "homeware"),
]


def _to_float(val):
    """Coerce a price-ish value to float; None if impossible.

    Handles ints, floats, and bare strings like "32.00" or "$28".
    """
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.strip().lstrip("$").replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def get_brand(d):
    meta = d.get("_meta")
    if isinstance(meta, dict) and meta.get("brand"):
        return meta["brand"]
    if d.get("brand"):
        return d["brand"]
    return "(unknown)"


def get_category(d):
    """Normalize free-text category -> canonical bucket."""
    raw = ""
    prod = d.get("product")
    if isinstance(prod, dict) and prod.get("category"):
        raw = prod["category"]
    elif d.get("category"):
        raw = d["category"]
    raw_l = str(raw).lower()
    for needle, bucket in CATEGORY_MAP:
        if needle in raw_l:
            return bucket
    return "other"


def _first_sku_price(d):
    """Pull a price from the first SKU across the known SKU locations."""
    prod = d.get("product")
    if isinstance(prod, dict):
        skus = prod.get("skus")
        if isinstance(skus, list):
            for s in skus:
                if isinstance(s, dict):
                    p = _to_float(s.get("price_usd") or s.get("price"))
                    if p:
                        return p
    parrot = d.get("parrot")
    if isinstance(parrot, dict):
        copy = parrot.get("copy")
        if isinstance(copy, dict):
            skus = copy.get("skus")
            if isinstance(skus, list):
                for s in skus:
                    if isinstance(s, dict):
                        p = _to_float(s.get("price_usd") or s.get("price"))
                        if p:
                            return p
    rabbit = d.get("rabbit")
    if isinstance(rabbit, dict):
        skus = rabbit.get("sku") or rabbit.get("skus")
        if isinstance(skus, list):
            for s in skus:
                if isinstance(s, dict):
                    p = _to_float(s.get("price_usd") or s.get("price"))
                    if p:
                        return p
    return None


def _bee_campaign(d):
    bee = d.get("bee")
    if isinstance(bee, dict):
        camp = bee.get("campaign")
        if isinstance(camp, dict):
            return camp
    return {}


def get_price(d):
    """Prefer a real per-SKU price; fall back to brand-level campaign price."""
    p = _first_sku_price(d)
    if p:
        return p
    camp = _bee_campaign(d)
    return _to_float(camp.get("price_usd"))


def get_cogs(d):
    """bee.campaign.cogs_usd, else product.cogs_usd."""
    camp = _bee_campaign(d)
    c = _to_float(camp.get("cogs_usd"))
    if c is not None:
        return c
    prod = d.get("product")
    if isinstance(prod, dict):
        return _to_float(prod.get("cogs_usd"))
    return None


def get_break_even_roas(d):
    camp = _bee_campaign(d)
    return _to_float(camp.get("break_even_roas"))


def get_actual_roas(d):
    """Median actual_roas across results.latest.ads (measured only)."""
    results = d.get("results")
    if not isinstance(results, dict):
        return None
    latest = results.get("latest")
    if not isinstance(latest, dict):
        return None
    ads = latest.get("ads")
    if not isinstance(ads, list):
        return None
    vals = []
    for a in ads:
        if isinstance(a, dict):
            r = _to_float(a.get("actual_roas"))
            if r:  # ignore 0 / None placeholders
                vals.append(r)
    if not vals:
        return None
    return round(statistics.median(vals), 2)


def has_actuals(d):
    results = d.get("results")
    if not isinstance(results, dict):
        return False
    return bool(results.get("latest") or results.get("snapshots"))


def _median(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return round(statistics.median(vals), 2)


def main():
    per_brand = []
    skipped = []

    for path in sorted(glob.glob(CUSTOMERS_GLOB)):
        rel = str(Path(path).relative_to(BASE))
        try:
            with open(path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:  # truncated / invalid json
            skipped.append({"file": rel, "reason": f"{type(e).__name__}: {e}"})
            continue
        if not isinstance(d, dict):
            skipped.append({"file": rel, "reason": "not an object"})
            continue
        try:
            per_brand.append({
                "brand": get_brand(d),
                "file": rel,
                "category": get_category(d),
                "price": get_price(d),
                "cogs": get_cogs(d),
                "break_even_roas": get_break_even_roas(d),
                "actual_roas": get_actual_roas(d),
                "has_actuals": has_actuals(d),
            })
        except Exception as e:  # never let one weird file kill the run
            skipped.append({"file": rel, "reason": f"normalize: {type(e).__name__}: {e}"})

    # bucket by category
    benchmarks = {}
    for cat in sorted({b["category"] for b in per_brand}):
        rows = [b for b in per_brand if b["category"] == cat]
        plan_vs_actual = [
            {
                "brand": b["brand"],
                "break_even_roas": b["break_even_roas"],
                "actual_roas": b["actual_roas"],
                "gap": (round(b["actual_roas"] - b["break_even_roas"], 2)
                        if (b["actual_roas"] is not None and b["break_even_roas"] is not None)
                        else None),
            }
            for b in rows if b["has_actuals"]
        ]
        benchmarks[cat] = {
            "brands": [b["brand"] for b in rows],
            "n": len(rows),
            "median_price": _median([b["price"] for b in rows]),
            "median_break_even_roas": _median([b["break_even_roas"] for b in rows]),
            "brands_with_actuals": sum(1 for b in rows if b["has_actuals"]),
            "plan_vs_actual": plan_vs_actual,
        }

    output = {
        "generated_from": CUSTOMERS_GLOB.replace(str(BASE), "<project>"),
        "brand_count": len(per_brand),
        "skipped": skipped,
        "per_brand": per_brand,
        "benchmarks": benchmarks,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    _print_markdown(benchmarks, per_brand, skipped)


def _fmt(v):
    return "—" if v is None else v


def _print_markdown(benchmarks, per_brand, skipped):
    print("# Brand OS — Portfolio Benchmarks\n")
    print(f"{len(per_brand)} brands loaded"
          + (f", {len(skipped)} skipped" if skipped else "") + ".\n")

    print("## By category\n")
    print("| Category | Brands | Median price | Median break-even ROAS | Brands w/ actuals |")
    print("|---|---|---|---|---|")
    for cat in sorted(benchmarks):
        b = benchmarks[cat]
        mp = f"${b['median_price']}" if b["median_price"] is not None else "—"
        print(f"| {cat} | {b['n']} | {mp} | "
              f"{_fmt(b['median_break_even_roas'])} | {b['brands_with_actuals']} |")

    print("\n## Plan vs Actual\n")
    rows = [pva for b in benchmarks.values() for pva in b["plan_vs_actual"]]
    if not rows:
        print("_No brand has measured actuals yet. Fill `results` in a "
              "context.json (start with your own store) to populate this._")
    else:
        print("| Brand | Plan break-even ROAS | Actual ROAS | Gap |")
        print("|---|---|---|---|")
        for r in rows:
            print(f"| {r['brand']} | {_fmt(r['break_even_roas'])} | "
                  f"{_fmt(r['actual_roas'])} | {_fmt(r['gap'])} |")

    if skipped:
        print("\n## Skipped\n")
        for s in skipped:
            print(f"- `{s['file']}` — {s['reason']}")


if __name__ == "__main__":
    main()
