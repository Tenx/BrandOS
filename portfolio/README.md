# Brand OS — Portfolio Layer

The **data moat**. Everything else in Brand OS (the 5 animal agents, the skills)
is visible surface area a competitor could copy. This layer is not: it turns each
brand's accumulated results into proprietary cross-portfolio truth that a generic
LLM can never reproduce.

## Run it

```bash
cd ~/.claude/projects/brand-os
python3 core/portfolio/aggregate.py
```

Read-only. It scans every `customers/*/context.json`, normalizes the messy
real-world shapes, and:

- prints a markdown summary (`## By category`, `## Plan vs Actual`) to stdout
- writes machine-readable `core/portfolio/benchmarks.json`

It **never crashes**: any unreadable/invalid file lands in `skipped[]` with a
reason instead of taking down the run. stdlib only — no dependencies, no network.

## What it reads

| Signal | Preferred source | Fallback |
|---|---|---|
| brand | `_meta.brand` | top-level `brand` |
| category | `product.category` | top-level `category` → mapped to a canonical bucket |
| price | `product.skus[].price_usd` / `.price` | `parrot.copy.skus[]` → `rabbit.sku[]` → `bee.campaign.price_usd` |
| cogs | `bee.campaign.cogs_usd` | `product.cogs_usd` |
| break-even ROAS | `bee.campaign.break_even_roas` | — |
| actual ROAS | median of `results.latest.ads[].actual_roas` (MEASURED) | — |

Bare-string prices (`"32.00"`, `"$28"`) are coerced. Missing `bee` / `product` /
`results`, or `elephant: {}`, are all tolerated.

## Why this is the moat (the Klaviyo lesson)

Klaviyo looks like an email tool. Its real, uncopyable asset is the **per-store
data layer nobody else sees** — every purchase and repeat purchase deepens a
profile that can't be exported. Eight years of that is why it went public.

Jasper died the opposite way: a thin wrapper over a model that only generated
text and sinks nothing. The moment ChatGPT shipped, it was free.

Brand OS's `results.*` block is our version of Klaviyo's layer:

- **Plan and actual are physically separate.** Plans live in `bee.campaign.*` and
  get overwritten every skill re-run. Actuals live in the top-level `results` key
  and are only ever written by a human/importer — so re-running a skill can never
  clobber real history. The record is **append-only** and only deepens.
- **`benchmarks.json` is proprietary cross-portfolio truth.** ChatGPT can write
  copy for one new brand; it cannot tell that new client "incense runs ~$28 median
  at ~2.2× break-even across our portfolio" — because it never sees the accumulated
  results. That gap is the entire difference between a report generator and a
  memory system, and the precondition for the ¥7000/month retainer to scale.

The longer a seller operates on Brand OS, the more `results` accrues, the sharper
the benchmarks, the deeper the moat.

## Seeding real data

Actuals start with **our own store** — HazumiCrafts (Etsy, ~$80K GMV). Pull one
month from Etsy Shop Manager → Stats and fill the `results` block in
`customers/hazumicrafts/context.json`. Even with `ads: []`, conversion rate and
per-SKU revenue prove the plan-vs-actual loop on real numbers before any client
sees it.
