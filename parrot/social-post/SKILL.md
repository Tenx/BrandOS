---
name: social-post
description: >
  Turn a product + copy into ready-to-post content for Instagram, Pinterest, TikTok, and Facebook.
  Use when the user wants to promote a new listing, drive traffic to their shop, or batch-create
  social content for one product across multiple platforms.
  Triggers: "发帖", "社媒内容", "ins文案", "pinterest", "tiktok文案", "facebook post",
  "social post", "content", "发布内容", "帮我写帖子", "social media".
---

# Social Post

Turn one product into platform-adapted posts for Instagram, Pinterest, TikTok, and Facebook.
Each post is ready to copy-paste — caption, hashtags, format notes included.

## Input

User provides one of:
- **Product copy** — paste from product-copy skill output (hook + story + bullets)
- **Product description** — freeform description of what it is and who it's for
- **Listing URL** — Etsy or Shopify URL; fetch and extract copy from the page

Plus optionally:
- **Platform(s)** — default: all four. User can specify just one or two.
- **Goal** — traffic to shop / brand awareness / product launch / seasonal push
- **Tone override** — if different from brand voice

If no product info provided, ask before proceeding.

## Steps

### 1. Fetch listing if URL provided

```bash
opencli browser main open "<listing_url>"
opencli browser main extract
```

Extract: product name, key features, price, any lifestyle language already in the listing.

### 2. Adapt per platform

**Instagram**
- Caption length: 150–300 words
- Structure: hook (1 line) → story/scene (2–3 sentences) → CTA (1 line) → hashtags (separate block)
- Hashtags: 15–20, mix broad (#handmade, #slowfashion) + niche (#crochetlover, #etsyseller) + seasonal
- Visual suggestion: describe the ideal shot (flat lay / lifestyle / model close-up)

**Pinterest**
- Title: 50–100 chars, keyword-first (Pinterest is a search engine)
- Description: 200–500 chars, front-load keywords, end with CTA
- Board suggestion: which board category this fits
- Hashtags: 2–5 only (Pinterest penalizes hashtag spam)

**TikTok**
- Script outline (not full script): hook (3 sec) → show product (5–10 sec) → key benefit (5 sec) → CTA (3 sec)
- Caption: under 150 chars + 3–5 hashtags
- Sound suggestion: vibe/mood description for background audio
- Text overlay suggestion: what to put on screen

**Facebook**
- Post length: 40–80 words (shorter than Instagram)
- Conversational tone, direct question or relatable opener
- CTA with link placeholder: "Shop here → [link]"
- No hashtags or max 2–3

### 3. Batch or single

If user asks for a **content batch** (e.g. "4 posts for this week"), generate:
- Day 1: product reveal (Instagram + Pinterest)
- Day 2: behind-the-scenes / process (TikTok script outline)
- Day 3: lifestyle/use case (Instagram)
- Day 4: social proof / customer scenario (Facebook)

## Output

```
## 📱 Social Post — [Product Name]

### instagram
[Caption 150–300 words]

Hashtags:
#[tag] #[tag] #[tag] ... (15–20)

Visual: [shot description]

---

### pinterest
Title: [keyword-first title]
Description: [200–500 chars]
Board: [suggested board]
Tags: #[tag] #[tag] #[tag]

---

### tiktok
Hook (0–3s): [what to say/show]
Product (3–13s): [what to show]
Benefit (13–18s): [key line]
CTA (18–21s): [closing line]

Caption: [under 150 chars] #[tag] #[tag] #[tag]
Sound vibe: [description]

---

### facebook
[40–80 words, conversational]
Shop here → [link]
```

Report is complete when all requested platforms have a filled section and the Instagram
caption hook does not start with the product name.
