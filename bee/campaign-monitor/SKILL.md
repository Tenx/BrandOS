---
name: campaign-monitor
description: >
  Pull live ad performance (Meta, Google, TikTok, Pinterest) for a running campaign, compare each
  metric against the kill/scale thresholds set by campaign-plan, and produce a daily human-readable
  tuning report: which ad sets to kill, which to scale, which creatives to swap, and how to move
  budget between phases. Read-only + recommend-only — it NEVER pauses, scales, or changes budget
  automatically. Built on the same official SDKs as ad-launcher (facebook-business, google-ads) +
  REST for TikTok/Pinterest, reading tokens from env/config.
  Semi-automatic: fetches data + recommends actions, human applies changes in the dashboard.
  Triggers: "监控广告", "投放复盘", "campaign monitor", "看数据", "广告数据", "调优",
  "kill rule", "要不要 kill", "要不要放量", "ROAS 怎么样", "每日复盘", "投放怎么样",
  "monitor campaign", "daily report", "素材要不要换", "预算要不要加".
---

# Campaign Monitor

Close the Bee loop. After `ad-launcher` creates a campaign and a human enables it, this skill runs
**daily** (or on demand): pull live numbers → compare against `campaign-plan` thresholds → output a
tuning report. This is the "mid-game" the AI was missing — it turns raw platform data into the same
kill/scale/swap decisions an experienced media buyer makes by hand.

**Read-only + recommend-only.** It fetches metrics and writes a report. It does **not** pause ad
sets, does not change budgets, does not swap creatives. Every action is a recommendation the human
applies in the platform dashboard. Same red line as the rest of Bee's execution layer.

## Input

From `context.json`:
- `bee.campaign.*` — break-even ROAS, phase ROAS targets, phase daily budgets, kill rules, phase
  (which week → which thresholds apply)
- `bee.campaign.decision_dashboard` — the metric → green/yellow/red table (the source of truth for
  thresholds; if absent, fall back to the defaults table below)
- `bee.execution.ads.*` — platforms, script paths, `campaign_id` per platform, `enabled_by_human`
- `rabbit.[platform].url` — landing page (for context in the report)
- `_meta.brand_dir` — where to write the report

Guards before running:
- If `bee.execution.ads.enabled_by_human` is `false` → tell the user nothing is live yet; there is
  no data to monitor. Do not proceed.
- If `campaign_id` is empty for a platform → skip that platform, note it in the report.
- If `bee.campaign` is empty → run `campaign-plan` first (thresholds come from there).

## What phase am I in?

Thresholds depend on the phase. Derive the phase from days-since-launch (or ask):
- **Phase 1 (Week 1–2, cold start)** — judge on CTR / CPM / add-to-cart, NOT ROAS. Buying data.
- **Phase 2 (Week 3–4, optimization)** — judge on ROAS vs break-even; kill waste.
- **Phase 3 (Month 2+, scale)** — judge on ROAS vs scale target + fatigue (frequency/CPM).

Applying Phase-2 ROAS kill rules during Phase 1 is the classic beginner error — it kills ad sets
before the algorithm has exited learning. The report must state which phase it assumed.

## Output location

Write a dated report to `customers/<brand>/ads/monitor/`:
```bash
mkdir -p ~/.claude/projects/brand-os/customers/<brand>/ads/monitor
# report: monitor/report_YYYY-MM-DD.md   (one per run, keep history for trend)
```

## Fetch scripts — read-only, per platform

Generate a `fetch_<platform>.py` alongside ad-launcher's `launch_<platform>.py` (or reuse if it
exists). Each fetch script must:
1. **Read token from env/config** — same vars as ad-launcher, never hardcoded.
2. **Only call read/insights endpoints** — no create/update/delete. If the SDK object exposes
   mutation methods, do not call them.
3. **Pull yesterday + last-7-day** metrics per ad set: spend, impressions, clicks, CTR, CPC, CPM,
   purchases/conversions, conversion value, ROAS, frequency (Meta), add-to-cart.
4. **Print JSON** to stdout (the skill parses it) — never write tokens to disk.

### Meta — `facebook-business` SDK, Insights (read-only)

```python
# fetch_meta.py — READ-ONLY. Pulls ad set insights. Makes no changes.
import os, json
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

TOKEN = os.environ["META_ACCESS_TOKEN"]
FacebookAdsApi.init(os.environ.get("META_APP_ID",""),
                    os.environ.get("META_APP_SECRET",""), TOKEN)
CAMPAIGN_ID = "<bee.execution.ads.scripts[meta].campaign_id>"

fields = ["adset_name","spend","impressions","clicks","ctr","cpc","cpm","frequency",
          "actions","action_values","purchase_roas"]
rows = []
for adset in Campaign(CAMPAIGN_ID).get_ad_sets(fields=["name"]):
    ins = AdSet(adset["id"]).get_insights(
        fields=fields, params={"date_preset":"last_7d","level":"adset"})
    for r in ins:
        rows.append(dict(r))
print(json.dumps({"platform":"meta","campaign_id":CAMPAIGN_ID,"adsets":rows}, indent=2))
# No create/update/delete calls anywhere in this file.
```

### Google — `google-ads` SDK, GAQL report (read-only)

Run a `search`/`search_stream` GAQL query over `ad_group` + `metrics` (cost_micros, clicks,
impressions, ctr, average_cpc, conversions, conversions_value) for the campaign. `search` is
read-only; never call `mutate_*`. Config from `google-ads.yaml` at the standard path.

### TikTok — Business API `/report/integrated/get/` (read-only)

REST GET/POST to the reporting endpoint with `advertiser_id` + `campaign_id`, dimensions
`["adgroup_id"]`, metrics `["spend","impressions","clicks","ctr","cpc","conversion","cost_per_conversion","complete_payment_roas"]`.
Token + advertiser_id from env. Report endpoints only — no `/adgroup/update/`.

### Pinterest — API v5 analytics (read-only)

REST GET `/v5/ad_accounts/{id}/campaigns/{campaign_id}/analytics` (or ad-group analytics) with
columns `SPEND_IN_DOLLAR, IMPRESSION_1, CLICKTHROUGH_1, CTR, CPC_IN_DOLLAR, TOTAL_CONVERSIONS,
TOTAL_ORDER_VALUE_IN_DOLLAR, ROAS`. Remember Pinterest's 30-day click default — normalize to 7-day
attribution before comparing to other platforms.

## Steps — evaluate against thresholds

### 1. Load thresholds
From `bee.campaign.decision_dashboard` if present, else the defaults below (mirrors campaign-plan):

| Metric | Green | Yellow | Red → recommended action |
|---|---|---|---|
| ROAS (Phase 2+) | > target | within 20% of break-even | < break-even for 7 days → **recommend pause + diagnose** |
| CTR (Phase 1) | > 2% Meta / > 0.5% Pinterest | 1–2% | < 1% after 3 days → **recommend swap creative** |
| CPC | stable/falling | +20% WoW | +50% → **recommend expand targeting (fatigue)** |
| Frequency (Meta) | < 2 | 2–3 | > 3 → **recommend new creative / new audience** |
| CPA vs break-even | ≤ break-even CPA | ≤ 1.5× | > 3× CPA with 0 conversions → **recommend pause ad set** |
| Spend pace | on target | ±20% | underspend → **recommend loosen targeting**; overspend → **recommend budget cap** |

### 2. Classify every ad set
For each ad set, compute its metrics and tag each metric green/yellow/red. Then assign the ad set an
overall recommendation, phase-aware:
- **KILL** — Phase 2+ ad set below break-even 7 days, or >3× CPA with 0 conversions.
- **SWAP CREATIVE** — CTR red, or Meta frequency > 3 (fatigue) with declining CTR.
- **SCALE** — ROAS above target (Phase 3) → recommend +20% daily budget max per 3 days (never more,
  to protect learning).
- **EXPAND** — CPC red / audience saturated → recommend broader targeting or new interest stack.
- **HOLD** — still in Phase 1 learning window, or all-green and stable → do nothing, keep feeding.

### 3. Budget-move suggestion
If some ad sets are SCALE and others are KILL, suggest reallocating the killed budget to winners —
but respect the phase daily-budget cap from `campaign-plan` and the +20%/3-day scale ceiling. This is
a **suggested** reallocation the human applies manually; the script does not move money.

### 4. Trend note
Compare today's report to the previous `report_*.md` in `monitor/` (if any): is ROAS improving or
decaying? Is CPC creeping up (early fatigue)? A single day is noise — flag direction over 3+ days
before recommending drastic action.

## Output

```
## 🐝 Campaign Monitor — [Brand] — [YYYY-MM-DD] — assumed Phase [1/2/3]

### snapshot (last 7d)
| Platform | Spend | ROAS | Break-even | CTR | CPC | Freq | Status |
|----------|-------|------|-----------|-----|-----|------|--------|
| Meta | $[x] | [x]× | [b]× | [x]% | $[x] | [x] | 🟢/🟡/🔴 |
| Pinterest | ... |

### per ad set — recommendations
| Ad set | Spend | ROAS/CPA | Flag | Recommended action (manual) |
|--------|-------|----------|------|------------------------------|
| [name] | $[x] | [x]× | 🔴 | KILL — below break-even 7d, pause in Ads Manager |
| [name] | $[x] | [x]× | 🟢 | SCALE — +20% daily budget (max), ROAS > target |
| [name] | $[x] | — | 🟡 | HOLD — still in Phase 1 learning, keep feeding |

### budget move (suggested, apply manually)
Free up $[x]/day from [killed ad sets] → add to [winners], within phase cap $[cap]/day.

### creative
[Which creatives to swap and why — CTR / frequency signal]

### trend vs [prev date]
ROAS [↑/↓/flat], CPC [↑/↓/flat] — [1-line read; noise vs real trend]

### today's 3 actions (human applies in dashboard)
1. [most important — e.g. "Pause 'AdSet-cold-broad' in Meta Ads Manager (ROAS 0.9× 7d)"]
2. [...]
3. [...]

### nothing-to-do check
[If all-green + in learning window: "Hold. No changes. Re-check tomorrow." — say it explicitly so
the human doesn't over-tweak. Over-editing during learning is a top failure mode.]
```

Report is complete when every live ad set has a phase-aware flag + a concrete manual action, ROAS is
compared to break-even, and the "today's 3 actions" list is specific (names + thresholds, not "check
performance").

## Red lines (半自动)

- **Read-only fetch** — only insights/report/analytics endpoints; no create/update/delete calls
- **Recommend-only** — every kill/scale/swap/budget-move is a suggestion the human applies manually
- **Never auto-pause, never auto-scale, never auto-move budget**
- **Tokens from env/config, never written to files** or committed
- **Phase-aware** — do not apply Phase-2 ROAS kill rules during Phase-1 learning
- **Direction over noise** — flag 3+ day trends before recommending drastic cuts

## Reuses

- `campaign-plan` — kill/scale thresholds, phase budgets, break-even ROAS (source of truth)
- `ad-launcher` — `campaign_id` per platform + same token env vars; fetch scripts sit beside launch
  scripts
- `ad-creative-brief` — when a SWAP CREATIVE is recommended, point back to it for the new variant
- **Official SDKs**: `facebook-business` (Meta), `google-ads` (Google); REST for TikTok/Pinterest

## Dry-run validation (no ad account, zero risk)

Same stubbing pattern as ad-launcher, but assert the script is **read-only**:
- Stub the SDK / `requests` so any call to a mutation method/endpoint (`create_*`, `update_*`,
  `mutate_*`, `/update/`, DELETE) raises `AssertionError` — proves the fetch script never mutates.
- Feed canned insights JSON and assert the evaluator emits the right flag (e.g. ROAS 0.9× in Phase 2
  → KILL; CTR 0.6% Meta Phase 1 → SWAP CREATIVE; ROAS above scale target → SCALE +20% cap).
- **Token guard** — run with no env tokens; must raise `KeyError` before any API call.

Pass criteria: fetch reaches only read endpoints, thresholds map to the right recommendation, phase
gating works, missing tokens fail fast.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "bee": {
    "execution": {
      "monitor": {
        "last_run": "YYYY-MM-DD",
        "assumed_phase": 1,
        "report_path": "customers/<brand>/ads/monitor/report_YYYY-MM-DD.md",
        "fetch_scripts": [
          { "platform": "meta", "path": "customers/<brand>/ads/fetch_meta.py", "read_only": true }
        ],
        "snapshot": {
          "meta": { "spend": 0, "roas": 0, "ctr": 0, "cpc": 0, "frequency": 0, "status": "green" }
        },
        "recommendations": [
          { "platform": "meta", "adset": "", "flag": "kill|swap|scale|expand|hold",
            "action": "", "applied_by_human": false }
        ]
      }
    }
  }
}
```
