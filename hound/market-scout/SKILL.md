---
name: market-scout
description: >
  Cross-border product research via Reddit, Instagram, and Etsy. Use when the user wants to
  validate a product niche, find buyer pain points, spot trending styles, or decide whether a
  category is worth entering. Triggers: "调研", "选品", "市场验证", "这个品类能做吗",
  "scout", "research niche", "trending", "what's selling".
---

# Market Scout

**Scout** a product category across three platforms and surface a decision-ready signal: is this
worth selling, and what angle wins?

## Input

User provides a **category keyword** — English or Chinese, broad or specific.
Examples: `"crochet top"`, `"手工蜡烛"`, `"macrame wall hanging"`.

If the user hasn't provided one, ask for it before proceeding.

## 服务/SaaS 类适配分支（非实物产品）

默认流程假设客户卖**实物商品**（三源 = Reddit + Instagram + Etsy）。若客户卖的是**服务 / SaaS / 课程 / 咨询 / 诊断**这类非实物产品（如 Brand OS 自己、¥699 跨境诊断、陪跑服务），三源适用性变化如下，按此调整后再跑 Steps：

| 源 | 实物 | 服务/SaaS | 说明 |
|----|------|-----------|------|
| **Reddit** | ✅ | ✅ **主信号源** | 搜目标用户聚集的 subreddit（如 r/Etsy、r/ecommerce、r/SaaS、r/Entrepreneur），挖痛点/抱怨/未满足需求。服务类几乎唯一的强需求信号就来自这里。 |
| **Instagram 视觉风格** | ✅ | ❌ N/A | 服务/SaaS 无实物视觉，hashtag 视觉风格分析对定位无意义。报告里标 `N/A — 非实物，无视觉风格可验证`。 |
| **Etsy 竞品定价** | ✅ | ❌ N/A → 改竞品官网 | 服务不在 Etsy 卖。改为搜**同类服务/工具的官网定价页**，对比订阅档位/套餐定价。能定位到竞品官网时：`opencli browser open "<竞品定价页URL>" --session "$S"` → `opencli browser extract --session "$S"`；定位不到则标 `N/A — 无 Etsy 对标，竞品定价见官网调研`。 |

**产出不变**：verdict / winning angle / buyer pain points / risks 照常给，只是数据源偏重 **Reddit + 竞品官网**，而非实物三源。`demand signals` 里 Instagram/Etsy 两行据实写 N/A + 原因（Step 3 允许带理由的 N/A）。`price_range` 填服务的定价区间（如引流款→后端的价格带）。

## Steps

### 1. Run three scouts in parallel

```bash
S="market-scout-$(date +%s)"  # opencli page 命令需 --session

# Reddit — buyer discussions, pain points, demand signals
# 注意：`opencli reddit search` 已废（返回 403 LOGIN_WALL），改走 browser 路径
opencli browser open "https://www.reddit.com/r/Etsy/search/?q=<keyword>&sort=top&type=link" --session "$S"
opencli browser extract --session "$S"

# Instagram — visual style trends via hashtag page
opencli browser open "https://www.instagram.com/explore/tags/<keyword_no_spaces>/" --session "$S"
opencli browser extract --session "$S"

# Etsy — top listings, pricing, competition density
opencli browser open "https://www.etsy.com/search?q=<keyword>&sort_on=score" --session "$S"
opencli browser extract --session "$S"
```

Run Reddit and browser opens simultaneously. Extract after each browser open.
A scout is complete when all three return output.

### 2. Extract signals

From each source pull only what changes the decision:

**Reddit**
- Top recurring questions or complaints → buyer pain points
- Posts with high score + high comments → validated demand
- Subreddits where the topic lives → where buyers gather

**Instagram**
- Dominant visual styles in post alt-text and captions → aesthetic direction
- Post density on the hashtag page → niche size and activity level

**Etsy**
- Product titles of top listings → winning keywords and positioning angles
- Ad vs organic ratio → competition intensity
- Price range across top results → viable price points

### 3. Output the scout report

Deliver a single structured report. Every section must be filled — no "N/A" or "data unavailable"
without a reason.

```
## 🐕 Market Scout — [keyword]

### verdict
[One sentence: enter / pass / enter with angle X]

### demand signals
- Reddit: [top subreddits + strongest posts]
- Instagram: [hashtag activity + dominant visual style]
- Etsy: [top listing titles + price range]

### buyer pain points
[3–5 bullet points from Reddit discussions]

### winning angle
[What style, price point, or positioning has the least competition and the most demand]

### risks
[Saturation level, seasonality, or platform-specific hazards]
```

The report is complete when all five sections are present and the verdict is a single actionable
sentence.

## Handoff → Parrot

After the scout report is done, pass these three things to `parrot/brand-story` or `parrot/product-copy`:

```
Winning angle:   [one line from scout report]
Buyer pain points: [top 2–3 bullets]
Price point:     [validated range from Etsy]
```

This gives Parrot the market context it needs to write on-target copy without guessing.

## Notes

**Reddit**: `opencli reddit search` 已废（403 LOGIN_WALL）；走 browser+session 路径抓公开搜索页，无需登录。

**Instagram**: uses `opencli browser` to fetch public hashtag pages — no login required.
For deeper profile data, optionally run:
```bash
S="market-scout-$(date +%s)"  # opencli page 命令需 --session
opencli browser open "https://www.instagram.com/<top_account>/" --session "$S"
opencli browser extract --session "$S"
```

**Etsy**: uses `opencli browser` to fetch public search results — no token required.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "hound": {
    "verdict": "enter | pass | enter with angle X",
    "winning_angle": "one-line positioning summary",
    "price_range": { "low": 0, "high": 0, "currency": "USD" },
    "buyer_pain_points": ["pain 1", "pain 2", "pain 3"],
    "top_keywords": ["keyword1", "keyword2", "keyword3"],
    "platform_signals": {
      "reddit": "subreddit + strongest post summary",
      "instagram": "hashtag activity + dominant visual style",
      "etsy": "top listing titles + competition density"
    },
    "risks": "one-line risk summary"
  }
}
```
