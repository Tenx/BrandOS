---
name: ad-launcher
description: >
  Read a campaign-plan output and generate platform Ads API launch scripts (Meta, Google,
  TikTok, Pinterest) that a human runs to create ad groups. Scripts default to PAUSED campaigns,
  read tokens from config/env (never hardcoded), and print a budget/audience/ROAS summary for
  review. Built on official SDKs (facebook-business, google-ads) + REST for TikTok/Pinterest.
  Semi-automatic: builds scripts, human enables in the platform dashboard.
  Triggers: "投放脚本", "建组", "launch ads", "ad launcher", "跑广告", "Meta 投放", "上广告",
  "Google Ads", "TikTok Ads", "Pinterest Ads", "广告 API", "真实投放", "launch campaign".
---

# Ad Launcher

Read `campaign-plan` output → generate one launch script per selected platform → human runs the
script to create **PAUSED** ad groups → human reviews and enables in the platform dashboard.
Semi-automatic by design: scripts create paused campaigns; nothing spends without human action.

## Input

From `context.json`:
- `bee.campaign.*` — platform(s), monthly budget, phases, break-even ROAS, kill rules
- `bee.audience.*` — Meta interests, TikTok audiences, Pinterest keywords, exclusions
- `bee.creative.*` — hero image brief, video hook, copy variants
- `rabbit.[platform].url` — landing page / product URL (destination)
- `_meta.brand_dir` — where to write the scripts

If `bee.campaign` is empty, run `campaign-plan` first (or ask the user to paste its output).

## Output location

Write scripts to `customers/<brand>/ads/`:
```bash
mkdir -p ~/.claude/projects/brand-os/customers/<brand>/ads
```
One script per selected platform: `launch_meta.py`, `launch_google.py`, `launch_tiktok.py`,
`launch_pinterest.py`.

## Common script contract (every platform)

Each generated script must:
1. **Read token from config/env** — never hardcode. Preferred sources:
   - env vars (e.g. `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`)
   - or a local config file (e.g. `~/.brandos/ads_config.json`) read at runtime
2. **Fill fields from context.json / args** — budget, audience, creative, destination URL
3. **Create everything as `status=PAUSED`** — campaign, ad set/group, ad all paused
4. **Print a review summary** before/after creation — daily budget, audience, break-even ROAS,
   phase-1 spend cap
5. **Require human to enable** — print instructions to review in the platform dashboard and flip
   to ACTIVE manually. The script does not enable, does not add budget, does not run kill rules.

Kill rules and budget caps from `campaign-plan` go into **script comments + the printed summary**,
not into any auto-executing logic.

## Steps — generate per platform

### Meta (Facebook + Instagram) — official `facebook-business` SDK

`pip install facebook-business`. Structure: Campaign → AdSet → Ad.

```python
# launch_meta.py — creates a PAUSED sales campaign. Review + enable in Ads Manager.
import os, json
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

# 1) token from env — never hardcoded
TOKEN = os.environ["META_ACCESS_TOKEN"]
ACCOUNT_ID = os.environ["META_AD_ACCOUNT_ID"]   # act_XXXXXXXX
APP_ID = os.environ.get("META_APP_ID", "")
APP_SECRET = os.environ.get("META_APP_SECRET", "")
FacebookAdsApi.init(APP_ID, APP_SECRET, TOKEN)

# 2) fields from context.json (filled at generation time)
DAILY_BUDGET_CENTS = 2000          # Phase 1 daily budget from campaign-plan, in cents
INTERESTS = ["<from bee.audience.meta_interests>"]
LANDING_URL = "<rabbit.[platform].url>"
BREAK_EVEN_ROAS = 1.75             # from bee.campaign.break_even_roas — review only

acct = AdAccount(ACCOUNT_ID)

# 3) PAUSED campaign
campaign = acct.create_campaign(params={
    "name": "BrandOS — <product> — Phase1",
    "objective": "OUTCOME_SALES",
    "status": "PAUSED",                       # <-- never auto-active
    "special_ad_categories": [],
})

# PAUSED ad set (targeting from audience-finder)
adset = acct.create_ad_set(params={
    "name": "AdSet — cold — interests",
    "campaign_id": campaign["id"],
    "daily_budget": DAILY_BUDGET_CENTS,
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "OFFSITE_CONVERSIONS",
    "status": "PAUSED",                       # <-- never auto-active
    "targeting": {"flexible_spec": [{"interests": []}]},  # fill INTERESTS ids
})

# 4) review summary
print(json.dumps({
    "campaign_id": campaign["id"], "adset_id": adset["id"], "status": "PAUSED",
    "daily_budget_usd": DAILY_BUDGET_CENTS / 100, "break_even_roas": BREAK_EVEN_ROAS,
    "landing": LANDING_URL,
}, indent=2))
# 5) NEXT: review in Meta Ads Manager, attach creative, flip to ACTIVE manually.
# KILL RULES (manual): pause any ad set spending >3x CPA with 0 conversions.
```

### Google — official `google-ads` SDK

`pip install google-ads`. Performance Max: campaign budget → PMax campaign → asset group +
audience signals. Uses `google-ads.yaml` (developer token, OAuth client, refresh token) — read
from the standard config path, never hardcoded. Create campaign with
`status=PAUSED` (`CampaignStatus.PAUSED`). Print budget / audience-signal / break-even ROAS
summary. Human enables in Google Ads UI.

### TikTok — Business API via `requests` (no official pip SDK)

REST calls to `https://business-api.tiktok.com/open_api/v1.3/`. Structure:
campaign → adgroup (prefer **Spark Ads** boosting an organic post) → ad.
- Access token + advertiser_id from env (`TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID`)
- Create with `operation_status="DISABLE"` (paused equivalent)
- Print summary; human enables in TikTok Ads Manager

### Pinterest — API v5 via `requests` (no official pip SDK)

REST calls to `https://api.pinterest.com/v5/`. Structure: campaign → ad group → pin promotion.
- Access token from env (`PINTEREST_ACCESS_TOKEN`, `PINTEREST_AD_ACCOUNT_ID`)
- Create campaign in `PAUSED` status
- **45-day lead-time reminder**: for seasonal pushes, schedule ad group start ~45 days before peak
- Print summary; human enables in Pinterest Ads Manager

## Output

```
## 🐝 Ad Launcher — [Platforms]

### scripts generated
| Platform | Script path | SDK/API | Default status |
|----------|-------------|---------|----------------|
| Meta | customers/<brand>/ads/launch_meta.py | facebook-business | PAUSED |
| Google | .../launch_google.py | google-ads | PAUSED |
| TikTok | .../launch_tiktok.py | REST | DISABLE |
| Pinterest | .../launch_pinterest.py | REST | PAUSED |

### per-platform summary
**Meta** — daily budget $[Phase1], audience [interests], target break-even ROAS [x], dest [url]
**Google** — ...
...

### token setup
Set env vars before running (never commit these):
export META_ACCESS_TOKEN=... / META_AD_ACCOUNT_ID=act_...
export TIKTOK_ACCESS_TOKEN=... / TIKTOK_ADVERTISER_ID=...
export PINTEREST_ACCESS_TOKEN=... / PINTEREST_AD_ACCOUNT_ID=...
Google: configure google-ads.yaml at the standard path.

### run instructions
1. Install SDKs: pip install facebook-business google-ads
2. Set tokens (above)
3. Run: python customers/<brand>/ads/launch_meta.py
4. Script creates a PAUSED campaign + prints summary
5. Review in the platform dashboard, attach creative, flip to ACTIVE manually

### dry-run validation (no ad account, zero risk)
Before touching a real ad account, verify a generated script reaches the create-campaign call
with the right fields (PAUSED status, correct budget/ROAS) using **stubbed SDK/HTTP** — no real
API calls, no spend. Verified this pattern on emotions' `launch_meta.py` + `launch_pinterest.py`.

- **Meta (facebook-business)** — stub the SDK modules via `sys.modules` before import, feed fake
  env tokens, and record the params passed to `create_campaign` / `create_ad_set`:
  ```python
  import sys, types, os
  os.environ.update(META_ACCESS_TOKEN="x", META_AD_ACCOUNT_ID="act_x")
  calls = []
  fb = types.ModuleType("facebook_business")
  api = types.ModuleType("facebook_business.api")
  api.FacebookAdsApi = type("A", (), {"init": staticmethod(lambda *a, **k: None)})
  acc = types.ModuleType("facebook_business.adobjects.adaccount")
  class _AdAccount:
      def __init__(self, *a): pass
      def create_campaign(self, params): calls.append(("campaign", params)); return {"id": "c1"}
      def create_ad_set(self, params): calls.append(("adset", params)); return {"id": "a1"}
  acc.AdAccount = _AdAccount
  sys.modules.update({"facebook_business": fb, "facebook_business.api": api,
                      "facebook_business.adobjects.adaccount": acc})
  exec(open("customers/<brand>/ads/launch_meta.py").read())
  assert all(p.get("status") == "PAUSED" for _, p in calls)   # every object PAUSED
  ```
- **Pinterest / TikTok (REST via requests)** — monkeypatch `requests.post` to capture URL + JSON
  body and return a canned `{"items":[{"data":{"id":"..."}}]}`; assert `status == "PAUSED"`
  (Pinterest) / `operation_status == "DISABLE"` (TikTok) and budget matches Phase-1.
- **Token guard check** — run the script with **no** env tokens set; it must raise `KeyError`
  on `os.environ[...]` *before* any API call. This proves zero accidental spend on a misconfig.

Pass criteria: script reaches create-campaign with `status=PAUSED`, budget/ROAS match
`campaign-plan`, and missing tokens fail fast.

### first action
[e.g. "Run launch_meta.py, verify PAUSED campaign + budget in Ads Manager"]
```

Report is complete when a script exists for each selected platform, each defaults to PAUSED,
reads tokens from env/config, and prints a budget/audience/ROAS summary.

## Red lines (半自动)

- **Scripts create PAUSED campaigns** — never auto-active
- **No auto-enable, no auto-budget-increase** — human flips to ACTIVE in the dashboard
- **Tokens from config/env, never written into files** or committed
- **Kill rules are manual** — documented in comments + summary, not auto-executed

## Reuses

- `campaign-plan` — break-even ROAS + phase budgets map directly to script fields
- `audience-finder` — targeting parameters (interests/keywords/exclusions)
- **Official SDKs**: `facebook-business` (Meta), `google-ads` (Google); REST for TikTok/Pinterest

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "bee": {
    "execution": {
      "ads": {
        "platforms": ["meta", "google", "tiktok", "pinterest"],
        "scripts": [
          { "platform": "meta", "path": "customers/<brand>/ads/launch_meta.py",
            "default_status": "PAUSED", "campaign_id": "" }
        ],
        "phase1_daily_budget_usd": 0,
        "break_even_roas": 0,
        "enabled_by_human": false
      }
    }
  }
}
```
