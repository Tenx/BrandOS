---
name: product-copy
description: >
  Write platform-neutral product copy for one SKU: hook sentence, bullet points, material/craft
  description, and emotional story paragraph. Output feeds directly into Rabbit listing skills
  (Etsy, Amazon, Shopify, Ozon) without rewriting. Use when the user has a new product and needs
  copy before publishing to any platform.
  Triggers: "产品文案", "产品描述", "卖点", "写一下这个产品", "product copy", "product description",
  "bullet points", "listing copy", "写文案".
---

# Product Copy

Write one product's core copy — hook, bullets, story, specs — once. Feed it to any platform's
listing skill without rewriting from scratch.

## Input

User provides:
- **Product name / type** — e.g. "crochet crop top", "soy wax candle", "macrame plant hanger"
- **Key features** — materials, dimensions, handmade process, variations available
- **Target buyer** — who it's for and the occasion (gift? self-treat? home decor?)
- **Price point** (optional) — helps calibrate language register (budget / mid / premium)
- **Brand voice** (optional) — paste from brand-story output, or describe in 2–3 words

If product name and features are missing, ask before proceeding.

## Steps

### 1. Extract copy angles

From inputs, identify:
- **Primary benefit** — what the buyer actually gets (feeling, result, occasion)
- **Proof point** — what makes it believable (material, process, detail)
- **Differentiator** — what sets this apart from mass-produced alternatives

### 2. Write copy blocks

**Hook sentence (1 sentence)**
— Opens with the buyer's desire or occasion, not the product name
— No "handmade with love", no "perfect gift for"

**Bullet points (5 bullets)**
— Format: [Feature] — [Buyer benefit]
— Mix: 2 material/craft facts + 2 use/feel benefits + 1 care/sizing/practical
— Each bullet standalone readable, no "and" chains

**Story paragraph (60–100 words)**
— Narrative version of the product: origin of the design, how it's made, what it's like to own it
— Platform-neutral: works as Etsy description opener, Amazon A+ text, Shopify product blurb

**Specs block**
— Material, dimensions, care instructions, available variations
— Bullet format, factual only

### 3. Platform adaptation notes

Flag any copy blocks that need adjustment per platform:
- **Amazon**: bullet points must start with capital, under 200 chars each; story paragraph → A+ Content
- **Etsy**: story paragraph goes first; no HTML; keyword density matters (handled by Rabbit)
- **Shopify**: story paragraph as hero text; specs in collapsible accordion
- **Ozon**: all copy needs Russian translation; specs format is strict (handled by Rabbit)

## Output

```
## 📦 Product Copy — [Product Name]

### hook
[One sentence]

### bullets
- [Feature] — [benefit]
- [Feature] — [benefit]
- [Feature] — [benefit]
- [Feature] — [benefit]
- [Feature] — [benefit]

### story
[60–100 words]

### specs
- Material: ...
- Dimensions: ...
- Care: ...
- Variations: ...

### platform notes
[Any flags for Amazon / Etsy / Shopify / Ozon adaptation]
```

Report is complete when all four blocks are filled and the hook sentence does not
start with the product name or "handmade".
