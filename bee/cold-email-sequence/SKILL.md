---
name: cold-email-sequence
description: >
  Given a recipient list, design a 3-email cold outreach sequence, personalize with variables,
  create Gmail drafts (not direct sends) for human review, and track follow-ups. Uses a Gmail
  MCP server (draft_email tool) for drafting. Semi-automatic: builds drafts, human confirms before send.
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

Create Gmail **drafts** (never sends) via a **Gmail MCP server**. Verified working:
[`@gongrzhe/server-gmail-autoauth-mcp`](https://github.com/gongrzhe/server-gmail-autoauth-mcp).
It handles OAuth + any proxy itself. **Note:** the actual draft tool name exposed is
`draft_email` (surfaced as `mcp__gmail__draft_email`), not `create_draft`.

Add it to the project's MCP config (`.mcp.json` or the project entry in `~/.claude.json`):

```json
{
  "mcpServers": {
    "gmail": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
      "env": {
        "HTTPS_PROXY": "http://<your-proxy-host>:<port>",
        "HTTP_PROXY": "http://<your-proxy-host>:<port>",
        "NO_PROXY": "localhost,127.0.0.1"
      }
    }
  }
}
```

> If your network blocks direct access to `googleapis.com` (e.g. a corporate firewall), the
> `HTTPS_PROXY`/`HTTP_PROXY` env above routes the MCP through a local proxy to reach Gmail.
> On an unrestricted network you can drop the `env` block. OAuth creds live in `~/.gmail-mcp/`.
> After changing MCP config or refreshing credentials, **restart the client** — an
> already-running MCP process holds its startup-time token and a mid-session kill won't reconnect.

Then, per recipient, call the MCP `draft_email` tool with the personalized fields:

- `to`: recipient email
- `subject`: personalized subject (e.g. `Quick idea for {{handle}}`)
- `body`: the filled email body (variables already substituted)

- Create one draft per recipient (or small batches), variables already filled in the body
- Present the created draft IDs for human review
- Only after explicit confirmation does the human send (from the Gmail UI)

Default action is **draft**, never direct send — use `draft_email`, never a send tool.

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
Created [N] drafts via the Gmail MCP `draft_email` (NOT sent). Review then confirm to send.

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

- **Gmail MCP** (`@gongrzhe/server-gmail-autoauth-mcp`) — `draft_email` for delivery. This skill
  orchestrates the sequence; the MCP handles OAuth, proxy, and draft creation.

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
