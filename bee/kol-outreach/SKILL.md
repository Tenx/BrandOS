---
name: kol-outreach
description: >
  Discover influencers/creators, tier them, generate personalized outreach (DM + email),
  and run a semi-automatic follow-up sequence. Finds candidates via opencli (logged-in Chrome)
  or a user-supplied list, scores by fit, drafts one-per-creator messages, and stops before
  sending for human confirmation. Use when the user wants to reach out to KOLs / creators for
  gifting, affiliate, or whitelisting deals.
  Triggers: "红人", "KOL", "达人", "网红", "influencer", "creator outreach", "找红人",
  "达人合作", "寄样", "affiliate", "whitelisting", "红人触达", "reach out to creators".
---

# KOL Outreach

Discover creators → tier them → generate personalized outreach → semi-automatic send → follow-up.
Semi-automatic by design: this skill drafts everything and stops **before** sending. A human
reviews and clicks send.

## Input

User provides:
- **Product / brand** — from `context.json: parrot.copy.hook`, `parrot.brand.*`, or describe
- **Target platform(s)** — Instagram / TikTok / 小红书 (default: Instagram)
- **Budget tier** — paid collab (has budget) vs free gifting (寄样) — sets the CTA offer
- **Creator list (optional)** — CSV/table of handles the user already has (skips discovery)
- **Search seed (optional)** — hashtag or keyword to discover from (e.g. `#soycandles`)

If product/brand and target platform are both missing, ask before proceeding.

## Steps

### 1. Discover candidates (two paths)

**Path A — opencli search** (no list provided)

Drive the already-logged-in Chrome to public hashtag/keyword pages, extract creator signals.
Mirrors the `hound/market-scout` Instagram/TikTok pattern.

```bash
# Instagram hashtag page
opencli browser main open "https://www.instagram.com/explore/tags/<seed_no_spaces>/"
opencli browser main extract

# Open a promising creator profile for follower count + bio + external link
opencli browser main open "https://www.instagram.com/<handle>/"
opencli browser main extract

# TikTok
opencli browser main open "https://www.tiktok.com/tag/<seed_no_spaces>"
opencli browser main extract
```

From each profile extract: `handle`, follower count, bio, external link, and any public email
(often in bio or a "for business: …" line). Assemble a candidates table.

**Path B — user-supplied list**

Read the CSV/table the user provides. Expected columns (fill what's available):
`handle, platform, followers, email, niche, notes`.

### 2. Tier and score

Bucket by follower count:
- **nano** — <10k (highest engagement, cheapest, best for gifting)
- **micro** — 10k–100k (sweet spot for conversion + reach)
- **mid** — 100k–500k (reach plays, usually paid)

Score each candidate for priority using:
- **Follower-to-engagement ratio** — high engagement > raw follower count
- **Niche relevance** — how closely their content matches the product
- **Already selling / affiliate signals** — do they tag products, use affiliate links?

Output a priority ranking (High / Med / Low), not just raw numbers.

### 3. Generate personalized outreach

One message per creator — reference something specific about their content so it never reads
as a mass template. Two carriers:

**DM (Instagram / TikTok / 小红书)**
- Short, conversational, mobile-readable
- Reference a specific recent post or their niche
- One clear CTA matched to budget tier: gifting (寄样) / affiliate commission / whitelisting
- No links in the first DM on IG/TikTok (spam filters) — offer to send details on reply

**Email (creators with a public business email)**
- More formal, full value proposition
- Hand off to `cold-email-sequence` for the actual draft + Gmail send

### 4. Follow-up sequence

Plan a 3-touch cadence per creator, tracked by status:
- **D0** — first touch (DM or email)
- **D3** — follow-up 1 (add social proof / restate the offer)
- **D7** — follow-up 2 (soft close / create mild scarcity)
- Mark each as `no_response` / `replied` / `partnered`

### 5. Semi-automatic send (human confirms)

For DM sending, prepare opencli commands but **stop before clicking send**:

```bash
# Open the creator's DM thread
opencli browser main open "https://www.instagram.com/direct/t/<thread_or_handle>"
# Locate the message box
opencli browser main find --css 'textarea[placeholder*="Message"]'
# Fill the drafted text (does NOT send)
opencli browser main type <ref> "<personalized DM text>"
# STOP — hand control to the human to review and click Send manually
```

Never call the send/submit action automatically. Provide the command list; the human executes
the final send after review. Do not mass-send.

## Output

```
## 🐝 KOL Outreach — [Product]

### candidates
| Handle | Platform | Tier | Followers | Email | Relevance | Priority |
|--------|----------|------|-----------|-------|-----------|----------|
| @...   | IG       | micro| 42k       | ...   | High      | 1        |

### outreach messages
**@handle_1** (DM)
[personalized 3–4 line DM referencing their content + CTA]

**@handle_2** (Email → cold-email-sequence)
[one-line note: hand to cold-email-sequence with this hook]

### follow-up calendar
| Handle | D0 | D3 | D7 | Status |
|--------|----|----|----|--------|
| @...   | DM | FU1| FU2| no_response |

### send commands (human confirms before sending)
[opencli command list per creator — stops at type, human clicks Send]

### first action
[Single next step: e.g. "Review 3 High-priority DMs, send manually"]
```

Report is complete when the candidates table has at least 5 rows (or all supplied), each
High-priority creator has a personalized message, and the follow-up calendar is filled.

## Red lines (半自动)

- **Never auto-click send** — drafts only; human reviews and sends each message
- **No mass blasting** — every message must be individually personalized
- Discovery uses public pages via logged-in Chrome; no scrapers, no credential harvesting

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "bee": {
    "execution": {
      "kol": {
        "platform": "instagram | tiktok | xiaohongshu",
        "candidates": [
          { "handle": "", "tier": "nano|micro|mid", "followers": 0,
            "email": "", "relevance": "High|Med|Low", "priority": 0,
            "status": "drafted|no_response|replied|partnered" }
        ],
        "messages_drafted": 0,
        "follow_up_cadence_days": [0, 3, 7]
      }
    }
  }
}
```
