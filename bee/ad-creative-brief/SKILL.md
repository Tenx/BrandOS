---
name: ad-creative-brief
description: >
  Generate ad creative briefs for any platform from product copy and audience data.
  Outputs image specs, video hook scripts, copy variants for A/B testing, and
  platform-specific format requirements. Use before producing ad creatives to ensure
  assets are built to spec and optimized for CTR.
  Triggers: "广告素材", "creative brief", "广告文案", "素材方案", "ad copy", "广告脚本",
  "A/B test", "广告创意", "投放素材", "ad creative".
---

# Ad Creative Brief

Turn product copy and audience insights into a production-ready creative brief.
Output feeds directly to a designer, video editor, or AI image tool.

## Input

User provides:
- **Product copy** — from product-copy skill, or describe the product
- **Audience** — from audience-finder skill, or describe target buyer in 2–3 sentences
- **Platform(s)** — Meta / Pinterest / TikTok / Google Shopping (default: all)
- **Goal** — awareness / traffic / conversion (default: conversion)
- **Budget signal** — small (under $50/day) / medium ($50–200/day) / scale ($200+/day)

If product copy is missing, ask before proceeding.

## Creative Strategy

Before writing briefs, identify the **primary creative angle** for this product:

- **Problem → Relief**: Lead with the pain, resolve with the product
- **Desire → Attainment**: Lead with the aspiration, show the product as the path
- **Social proof → Trust**: Lead with a result or reaction, build credibility
- **Curiosity gap**: Open a question the viewer needs to answer

Choose the angle that best matches the audience's purchase trigger from audience-finder.
If no audience data, default to Desire → Attainment for lifestyle/home products,
Problem → Relief for functional products.

## Steps

### 1. Write copy variants (A/B test pairs)

For each platform, write 2 headline variants and 2 body copy variants:

**Headline rules**
- Under 40 chars for Meta / TikTok (mobile truncation)
- Under 100 chars for Pinterest
- Lead with benefit or curiosity, never product name
- Variant A: emotional / lifestyle angle
- Variant B: functional / proof angle

**Body copy rules**
- Meta: 1–3 sentences, ends with implicit or explicit CTA
- Pinterest: 2–4 sentences, keyword-rich, soft CTA
- TikTok: not used (copy is on-screen overlay, handled in video brief)
- Google Shopping: not applicable (title/description from listing skills)

### 2. Image creative brief

**Static image (all platforms)**
- Hero shot description: subject, background, lighting, mood
- Text overlay: headline placement, font weight suggestion (bold / light)
- Platform crop specs:
  - Meta Feed: 1:1 (1080×1080) or 4:5 (1080×1350)
  - Meta Stories/Reels: 9:16 (1080×1920)
  - Pinterest: 2:3 (1000×1500)
  - TikTok: 9:16 (1080×1920)
- Color/mood: align with brand voice from brand-story if available

**Carousel (Meta only)**
- Card 1: hook / problem
- Card 2–4: features or use cases (one per card)
- Card 5: CTA + product shot

### 3. Video creative brief (TikTok + Meta Reels)

Structure every video brief in 4 acts:

**Hook (0–3s)** — must stop the scroll
- Visual: what appears on screen
- Audio: voiceover line or sound cue
- Text overlay: on-screen text
- Rule: no logo, no brand name in first 3 seconds

**Problem/Desire (3–8s)**
- What the viewer is feeling or missing
- Show don't tell

**Product reveal (8–18s)**
- Product in use or in context
- Key feature shown visually, not just described

**CTA (18–21s)**
- Single action: "Shop now", "Link in bio", "Find yours"
- On-screen text + voiceover

### 4. Budget-to-format recommendation

Match creative format to budget signal:
- **Small** (<$50/day): 1 static image per platform, test 2 headline variants, no video
- **Medium** ($50–200/day): 1 static + 1 video per platform, 2 copy variants each
- **Scale** ($200+/day): full creative matrix — 3 static, 2 video, 3 copy variants, carousel

## Output

```
## 🎨 Ad Creative Brief — [Product]

### creative angle
[Selected angle + one-line rationale]

### copy variants

**Headlines**
A (emotional): "[headline]"
B (functional): "[headline]"

**Body copy**
A: [1–3 sentences]
B: [1–3 sentences]

### image brief
Hero shot: [description]
Text overlay: [placement + weight]
Specs:
- Meta Feed: 1080×1080 or 1080×1350
- Meta Stories: 1080×1920
- Pinterest: 1000×1500
- TikTok: 1080×1920

### video brief (TikTok + Reels)
Hook (0–3s): [visual] | [audio/text]
Problem/Desire (3–8s): [description]
Product reveal (8–18s): [description]
CTA (18–21s): [text + voiceover]

### carousel (Meta)
Card 1: [hook]
Card 2: [feature/use case]
Card 3: [feature/use case]
Card 4: [feature/use case]
Card 5: [CTA]

### format recommendation
Budget level: [small/medium/scale]
Recommended: [which formats to produce first]
```

Report is complete when copy variants, image brief, and video brief are filled,
and format recommendation matches the stated budget signal.
