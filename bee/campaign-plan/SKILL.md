---
name: campaign-plan
description: >
  Build a complete ad campaign plan optimized for ROAS. Takes budget, platform, product,
  and audience inputs — outputs a phased launch plan with budget allocation, bid strategy,
  ROAS targets per phase, and decision rules for scaling or cutting.
  Use when the user is ready to launch ads and needs a structured spend plan.
  Triggers: "投放计划", "广告计划", "campaign", "怎么投", "预算分配", "ROAS",
  "campaign plan", "ad plan", "如何投放", "冷启动", "放量", "广告策略".
---

# Campaign Plan

Build a phased ad campaign plan around a single ROAS target.
Input: budget + platform + product + audience. Output: executable 3-phase plan.

## Input

User provides:
- **Product** — what they're advertising (paste product-copy hook, or describe)
- **Platform(s)** — Meta / Pinterest / TikTok / Google Shopping / Etsy Ads
- **Monthly budget** — total ad spend budget in USD
- **Current price** — product selling price
- **COGS estimate** — cost of goods (manufacturing + shipping), for break-even ROAS calc
- **Audience** — from audience-finder output, or describe target buyer
- **Creative assets** — from ad-creative-brief, or note what's available (images only / video / none)

If budget and price are missing, ask before proceeding.

## ROAS Framework

### Break-even ROAS

```
Break-even ROAS = Price / (Price - COGS)
```

Example: Price $28, COGS $8 → Break-even ROAS = 28 / 20 = 1.4×

Everything above break-even is profit. Set phase targets accordingly:
- Phase 1 (learning): accept ROAS at or slightly below break-even — buying data
- Phase 2 (optimization): hit break-even, improve toward target ROAS
- Phase 3 (scale): exceed target ROAS, increase spend while maintaining efficiency

### Target ROAS by product price tier

| Price | Minimum viable ROAS | Good ROAS | Scale ROAS |
|---|---|---|---|
| <$20 | 2.0× | 3.5× | 5×+ |
| $20–50 | 1.8× | 3.0× | 4×+ |
| $50–100 | 1.5× | 2.5× | 3.5×+ |
| $100+ | 1.3× | 2.0× | 3×+ |

## Steps

### 1. Calculate break-even and set ROAS targets

Compute break-even ROAS from user inputs. Set targets for each phase.
Flag if budget is too small to generate statistically meaningful data
(minimum: $15–20/day for Meta, $10/day for Pinterest, $20/day for TikTok).

### 2. Build 3-phase plan

**Phase 1 — Cold Start (Week 1–2)**
Goal: feed the algorithm, find converting audiences — NOT profit
- Budget: 40% of monthly budget
- Bid strategy: Lowest cost (let platform optimize)
- Audience: broad + 2–3 interest stacks from audience-finder
- Creative: test 2 static image variants (A/B headline test)
- Success metric: CPM, CTR, Add-to-cart rate (not ROAS yet)
- Kill rule: if CTR <1% after 3 days on Meta / <0.5% on Pinterest → swap creative

**Phase 2 — Optimization (Week 3–4)**
Goal: reach break-even ROAS, cut waste
- Budget: 35% of monthly budget
- Actions: kill underperforming ad sets, double budget on winners
- Bid strategy: Cost cap at break-even CPA
- Audience: narrow to best-performing segments from Phase 1
- Creative: introduce video if available
- Success metric: ROAS vs break-even target
- Kill rule: any ad set spending >3× CPA without conversion → pause

**Phase 3 — Scale (Month 2+)**
Goal: exceed target ROAS, increase spend
- Budget: remaining 25% + reinvest Phase 1–2 profits
- Bid strategy: Target ROAS bid
- Audience: lookalike audiences built from Phase 1–2 purchasers
- Creative: full creative matrix — new angles, seasonal variants
- Scaling rule: increase daily budget by max 20% every 3 days to avoid resetting learning
- Success metric: ROAS vs scale target; monitor frequency (>3× on Meta = creative fatigue)

### 3. Platform-specific notes

**Meta**
- Consolidate ad sets — too many split budget and slow learning (max 3–4 ad sets in Phase 1)
- Advantage+ Shopping Campaigns (ASC) viable for Phase 3 if catalog is set up
- Frequency cap: pause/refresh creative when frequency >3 on same audience

**Pinterest**
- Longer attribution window (30-day click default) — ROAS looks lower early; normalize to 7-day
- Promoted Pins get organic distribution boost — good for awareness plays
- Seasonal content: pin 45 days before peak season (not 2 weeks like other platforms)

**TikTok**
- Spark Ads (boosting organic posts) outperform dark posts for new accounts
- TopView / Brand Takeover only viable at $200+/day budgets — skip in Phase 1–2
- Algorithm reset risk: avoid pausing campaigns for more than 48 hours

**Google Shopping**
- Performance Max campaign for Phase 1 — let Google find converting queries
- Add negative keywords after 2 weeks based on Search Terms report
- Smart Bidding needs 30–50 conversions to exit learning mode — plan budget accordingly

**Etsy Ads**
- Simplest platform: set daily budget, Etsy auto-bids on relevant searches
- Start at $5–10/day, increase by $2–3/day every week if ROAS >break-even
- Recommended listings to promote: highest-review, lowest-return items first

### 4. Decision dashboard

Define what to check weekly and what action each metric triggers:

| Metric | Check | Green | Yellow | Red → Action |
|---|---|---|---|---|
| ROAS | Weekly | >target | Within 20% of break-even | <break-even for 7 days → pause + diagnose |
| CTR | Daily (Phase 1) | >2% Meta, >0.5% Pinterest | 1–2% | <1% after 3 days → swap creative |
| CPC | Weekly | Stable or falling | +20% week-on-week | +50% → audience fatigue, expand targeting |
| Frequency | Weekly (Meta) | <2 | 2–3 | >3 → new creative or new audience |
| Spend pace | Daily | On target | ±20% | Underspend → loosen targeting; Overspend → add budget cap |

## Output

```
## 🐝 Campaign Plan — [Product] on [Platform]

### roas targets
Break-even ROAS: [calculated]
Phase 1 target: [accept losses for data]
Phase 2 target: [break-even]
Phase 3 target: [scale ROAS]

### budget allocation
Monthly budget: $[total]
Phase 1 (Week 1–2): $[amount] — [daily rate]
Phase 2 (Week 3–4): $[amount] — [daily rate]
Phase 3 (Month 2+): $[amount] — [daily rate]

### phase 1 — cold start
Bid strategy: [lowest cost / auto]
Audiences: [2–3 stacks from audience-finder]
Creatives: [which assets to use]
Kill rule: [specific CTR threshold + action]

### phase 2 — optimization
Bid strategy: [cost cap at break-even CPA]
Actions: [what to cut, what to double]
Creative change: [add video? new angle?]
Kill rule: [specific CPA threshold + action]

### phase 3 — scale
Bid strategy: [target ROAS]
Audience expansion: [lookalike description]
Scaling rule: [max % budget increase per interval]
Fatigue signal: [frequency / CPM threshold]

### platform notes
[Any platform-specific flags for this product/budget]

### decision dashboard
[Weekly metrics table with thresholds and actions]

### first action
[Single most important thing to do in the next 24 hours]
```

Report is complete when ROAS targets are calculated, all 3 phases have budget amounts,
and the first action is a specific executable step (not "set up ads").
