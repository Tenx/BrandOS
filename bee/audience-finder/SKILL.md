---
name: audience-finder
description: >
  Identify the best target audience for a product across ad platforms. Outputs buyer persona,
  interest targeting keywords, exclusion audiences, and platform priority ranking — ready to
  plug into Meta Ads, TikTok Ads, Pinterest Ads, or Google Shopping.
  Use when the user wants to know who to target before launching ads.
  Triggers: "受众", "目标人群", "targeting", "audience", "投给谁", "人群定向",
  "interest targeting", "受众定位", "who to target".
---

# Audience Finder

Define who to target before spending a dollar. Outputs platform-ready audience parameters
and a ranked list of where to find this buyer most efficiently.

## Input

User provides:
- **Product** — what they sell (paste from product-copy, or describe)
- **Price point** — helps determine platform fit (budget / mid / premium)
- **Current sales channel** — Etsy / Shopify / Amazon / Ozon / other
- **Any known buyer info** (optional) — age, gender, location, interests if already known

If product is missing, ask before proceeding.

## Steps

### 1. Build buyer persona

From product inputs, define the core buyer in 4 dimensions:

**Demographics**
- Age range, gender skew
- Geography: primary markets (US / UK / DE / AU / CA most common for cross-border)
- Household context: lives alone / family / homeowner

**Psychographics**
- Values and identity (e.g. "buys handmade to avoid fast fashion")
- Purchase trigger (gift / self-treat / home refresh / seasonal)
- Price sensitivity signal (impulse at $20 / considered at $50 / researched at $100+)

**Behavioral signals**
- What else do they buy? (adjacent brands and categories)
- Where do they discover products? (search / social scroll / Pinterest save)
- When do they buy? (seasonal peaks from trend-timer if available)

**Negative persona** — who NOT to target
- Characteristics that indicate low conversion (e.g. deal-hunters if premium product)

### 2. Map to platform targeting parameters

For each relevant platform, output specific targeting parameters:

**Meta (Facebook + Instagram)**
- Detailed interests: list 8–12 specific interest categories
- Lookalike seed: describe the ideal seed audience (e.g. "website purchasers", "email list")
- Exclusions: audiences to exclude
- Placement recommendation: Feed / Reels / Stories / Shopping

**Pinterest**
- Interest categories (Pinterest taxonomy)
- Keywords for keyword targeting (Pinterest is search-driven)
- Audience type: browse / search / actalike
- Board topics to target

**TikTok**
- Interest categories
- Hashtag audiences (content users engage with)
- Creator lookalike signals (describe creator profile type, not specific handles)
- Device/behavior: note if product skews iOS vs Android buyers

**Google Shopping** (for Shopify/WooCommerce sellers)
- Audience signals for Performance Max: describe in-market segments
- Negative keywords to exclude irrelevant traffic

### 3. Platform priority ranking

Score each platform 1–5 for this specific product based on:
- Buyer presence (is this audience active here?)
- Product-format fit (visual product → Pinterest/Instagram; impulse → TikTok)
- CPC efficiency at this price point
- Competition density

Output ranked recommendation with one-line rationale per platform.

## 服务/SaaS 类适配分支（非实物产品）

默认流程假设**实物商品 + 海外电商投流**（Meta / Pinterest / TikTok / Google Shopping，KPI = ROAS）。若客户卖的是**服务 / SaaS / 课程 / 咨询 / 诊断**（如 Brand OS、¥699 跨境诊断、陪跑），按以下调整 Step 2–3：

**1. 投放平台改中文内容生态（当目标客群在中国境内）**
Step 2 的 Meta/Pinterest/TikTok/Google Shopping 四位多半不适用（客群不在海外电商流量池）。改为：
- **小红书**（通常 #1）：搜索词定向（行业关键词，如"跨境电商/独立站/副业出海"）+ 薯条投搜索页与发现页；用真实案例/干货笔记做钩子。
- **视频号 / 公众号**（#2）：长内容（图文/视频）建立信任 → 引导私域（企微/社群）→ 转化；公众号沉淀私域复购。
- **B站**（#3）：教程/实操长视频（如全链 dogfood 录屏），视频中插 + 简介引流。
- **海外 SaaS 例外**：客群在海外时回到 **Meta / LinkedIn（B2B）/ Google Search（搜索意图）**，而非实物电商的 Pinterest/Shopping。

**2. KPI 换 CAC + LTV（替代 ROAS）**
- 实物看 ROAS / break-even ROAS；服务/SaaS 看 **CAC（获客成本）** 与 **LTV（客户终身价值）**。
- 服务常是「引流款 → 高价后端」漏斗（例：¥699 诊断 → ¥2000/hr 咨询 → ¥7000/月 陪跑）。**LTV 远高于单笔**，故**可承受比单笔价更高的 CAC**——别用单笔引流款价算 break-even。
- Output 里 `### platform priority` 的 `ROAS potential` 字段，服务分支下改成 **`CAC 效率 / LTV 潜力`**。

**3. Persona 是从业者/决策者本人**
buyer persona 四维照常，但对象是**采购决策者 / 从业者本人**（想做或在做该业务的人），不是终端消费者。触发点通常是"卡住了想找人问 / 想提效"，而非"想买个东西用/送礼"。

## Output

```
## 🎯 Audience Finder — [Product]

### buyer persona
Demographics: [age, gender, geo]
Psychographics: [values, trigger, price sensitivity]
Behavioral: [adjacent brands/categories, discovery channel, timing]
Negative: [who to exclude]

### meta targeting
Interests: [8–12 specific interests]
Lookalike seed: [description]
Exclusions: [audience exclusions]
Placement: [recommended placements]

### pinterest targeting
Interest categories: [list]
Keywords: [10–15 search keywords]
Audience type: [browse / search / actalike]

### tiktok targeting
Interest categories: [list]
Hashtag audiences: [content signals]
Behavioral note: [any device/behavior flags]

### google shopping signals
In-market segments: [description]
Negative keywords: [list]

### platform priority
1. [Platform] — [one-line rationale] — ROAS potential: [High/Med/Low]
2. [Platform] — ...
3. [Platform] — ...
4. [Platform] — ...

### recommended first platform
[Single recommendation for where to start, with budget threshold]
```

Report is complete when buyer persona and at least 2 platform targeting sections are filled,
and platform priority list names a clear #1 recommendation.
