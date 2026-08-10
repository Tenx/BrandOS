---
name: cold-email-sequence
description: >
  Given a recipient list, design a 3-email cold outreach sequence, personalize with variables,
  create Gmail drafts (not direct sends) for human review, and track follow-ups. Reuses the
  gmail skill for drafting/sending. Semi-automatic: builds drafts, human confirms before send.
  Use for creator gifting, wholesale/distribution, or partnership outreach by email.
  Triggers: "cold email", "邮件序列", "外联邮件", "群发邮件", "email sequence", "跟进邮件",
  "冷启动邮件", "批发邮件", "分销邮件", "email outreach", "follow-up email".
---

# Cold Email Sequence

Given a recipient list → design a tiered 3-email sequence → create Gmail **drafts** →
human reviews and sends → track follow-ups.
Semi-automatic by design: this skill builds drafts, it does not auto-send.

## Input

User provides:
- **Recipient list** — KOL emails (from `kol-outreach`), wholesale buyers, or partners.
  Columns: `first_name, email, handle (optional), recent_content (optional), notes`
- **Product / brand** — from `context.json: parrot.copy.hook`, `parrot.brand.*`, or describe
- **Goal** — gifting (寄样合作) / distribution (分销) / whitelisting
- **Prior context (optional)** — any existing reply thread to continue

If recipient list or product is missing, ask before proceeding.

## Steps

### 1. Design the 3-email sequence

**Initial (D0)** — personalized opener + value prop + soft CTA
- Line 1 references the recipient specifically (their content / shop / niche)
- One clear value proposition, matched to goal
- Soft CTA ("open to a quick chat?" / "want me to send a sample?")

**Follow-up 1 (D3)** — add social proof + concrete offer
- Reference the first email lightly (no guilt)
- Add proof (results, other partners, sample photos) and a concrete offer

**Follow-up 2 (D7)** — break-up email, mild scarcity
- Short, respectful close ("I'll stop here — reach out anytime")
- Optional light scarcity (limited sample batch / launch window)

### 2. Personalization variables

Fill from the recipient list and `context.json`:
- `{{first_name}}` — recipient
- `{{handle}}` — social handle if present
- `{{recent_content}}` — a specific post/product of theirs
- `{{product_hook}}` — from `parrot.copy.hook`

Every email must have at least one filled variable that is genuinely specific — no bare templates.

### 3. Compliance

- Real human signature (name + brand + reply-to)
- Clear identity — who you are and why you're reaching out
- Include an opt-out intent line ("not the right fit? just let me know and I'll leave you be")
- Avoid spam-trigger words (FREE!!!, guaranteed, $$$, ALL CAPS subject lines)
- **Send-volume guardrail**: for a new/cold sending domain, warm up — start ~10–20/day and ramp.
  Flag this to the user if the list is large.

### 4. Gmail semi-automatic send (drafts first)

Use the **gmail** skill's `draft` command to create Gmail **drafts** (never sends).
This requires the `modify` scope — set it once, then re-auth:

```bash
# one-time: upgrade scope + re-authenticate
python3 scripts/gmail_search.py scope --set modify
python3 scripts/gmail_search.py auth

# per recipient: write the personalized body to a temp file, then create a draft
#   (body-file keeps newlines + variables intact)
python3 scripts/gmail_search.py draft \
  --to "creator@example.com" \
  --subject "Quick idea for {{handle}}" \
  --body-file /tmp/email1_<recipient>.txt
```

- Create one draft per recipient (or small batches), variables already filled into the body file
- Present the created draft IDs for human review
- Only after explicit confirmation does the human send (from the Gmail UI)

Default action is **draft**, never direct send. The gmail skill has no send path.

### 5. Follow-up tracking

- Record `sent_at` and whether a reply came in
- If no reply by the cadence date (D3 / D7), surface the next email as ready-to-draft
- Stop the sequence for any recipient who replies or opts out

## Output

```
## 🐝 Cold Email Sequence — [Goal]

### email 1 — initial (D0)
Subject: [<40 chars, no spam words]
Body:
Hi {{first_name}},
[personalized opener referencing {{recent_content}}]
[value prop tied to {{product_hook}}]
[soft CTA]
— [signature]

### email 2 — follow-up 1 (D3)
Subject: ...
Body: ...

### email 3 — follow-up 2 / break-up (D7)
Subject: ...
Body: ...

### send calendar
| Recipient | Email | D0 | D3 | D7 | Status |
|-----------|-------|----|----|----|--------|
| {{first_name}} | ... | draft | — | — | drafted |

### gmail action
Created [N] drafts via gmail skill (NOT sent). Review then confirm to send.

### first action
[e.g. "Review 3 drafts in Gmail → send batch 1 (10 max/day for new domain)"]
```

Report is complete when all 3 email templates are written with variables, the send calendar
lists every recipient, and Gmail drafts are created (not sent).

## Red lines (半自动)

- **Default is draft, never direct send** — human confirms every send
- **Respect send frequency / warm-up** for cold domains; do not blast
- **Compliance always on** — identity, opt-out, no spam triggers

## Reuses

- **gmail** skill — draft/send/track. This skill orchestrates the sequence; gmail handles delivery.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "bee": {
    "execution": {
      "email": {
        "goal": "gifting | distribution | whitelisting",
        "recipients": [
          { "first_name": "", "email": "", "handle": "",
            "status": "drafted|sent|replied|opted_out",
            "sent_at": "", "next_touch": "D3|D7|done" }
        ],
        "sequence_days": [0, 3, 7],
        "drafts_created": 0,
        "sends_confirmed": 0
      }
    }
  }
}
```
