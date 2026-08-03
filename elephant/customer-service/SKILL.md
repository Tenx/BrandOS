---
name: customer-service
version: 2.0.0
title: Cross-Platform Customer Service Assistant
description: |
  End-to-end customer service workflow for cross-border sellers across multiple platforms:
  - Etsy: read/reply via opencli browser (no API key needed)
  - Amazon: read/reply via Seller Central messaging (opencli browser)
  - Shopify: read/reply via Admin API or opencli browser
  - Universal: generate professional reply drafts based on shop branding and message type

triggers:
  - "客服"
  - "回复消息"
  - "买家消息"
  - "reply to messages"
  - "check customer messages"
  - "handle buyer inquiry"
  - "回复买家"
  - "处理客诉"

environment:
  required_tools:
    - opencli

config_file: shop_config.yaml
---

# Customer Service

Handle buyer messages across Etsy, Amazon, and Shopify in one workflow.
Read → Classify → Draft reply → Confirm → Send.

## Supported Platforms

| Platform | Read method | Send method |
|---|---|---|
| Etsy | opencli browser → etsy.com/messages | opencli browser click + type |
| Amazon | opencli browser → sellercentral.amazon.com/messaging | opencli browser click + type |
| Shopify | Admin API or opencli browser | Admin API or opencli browser |

## Message Types & Reply Strategy

Classify each message before drafting a reply:

| Type | Signal phrases | Reply goal |
|---|---|---|
| **Order status** | "where is my order", "tracking", "when will it arrive" | Reassure + provide tracking |
| **Product question** | "does it come in", "what size", "is it safe for" | Answer directly + soft upsell |
| **Complaint** | "damaged", "not as described", "wrong item" | Apologize → resolve → retain |
| **Return/refund** | "want to return", "refund", "cancel" | Follow platform policy → resolve gracefully |
| **Review fishing** | positive message, no specific issue | Thank → note happy customer for review request |
| **Spam / irrelevant** | unrelated to order or product | Flag, do not reply |

## Steps

### 1. Read messages

**Etsy:**
```bash
opencli browser main open "https://www.etsy.com/messages"
opencli browser main extract
```

**Amazon:**
```bash
opencli browser main open "https://sellercentral.amazon.com/messaging/inbox"
opencli browser main extract
```

**Shopify (if Admin API configured):**
```bash
# Read orders with open notes/customer contact
GET /admin/api/2024-01/orders.json?status=open&fields=id,email,note,customer
# Credentials from ~/.customer-service/shop_config.yaml
```

Extract: sender name, order reference (if any), message body, timestamp.

### 2. Classify and prioritize

Process messages in this order:
1. Complaints and return/refund requests — highest urgency
2. Order status questions — time-sensitive
3. Product questions — standard
4. Everything else

### 3. Draft reply

Use shop config for tone and brand voice (read from `~/.customer-service/shop_config.yaml`).

**Reply principles:**
- First sentence: acknowledge the specific issue — never generic "thank you for contacting us"
- Second: resolve or give a clear next step
- Close: warm but not gushing — match brand voice
- Length: 3–5 sentences; never more than 8

**Platform tone:**
- Etsy: casual and personal; buyers expect handmade seller warmth
- Amazon: more formal; never mention Etsy or other platforms in replies
- Shopify: match brand voice from brand-story config if available

**Common reply starters (adapt to brand voice):**

*Order status:*
> Your order is on its way — tracking [X] should show movement within [Y] days. Cross-border shipping to [country] typically takes [range].

*Complaint (damaged):*
> I'm sorry your [product] arrived damaged. I'll send a replacement right away — no need to return the original. Could you share a photo so I can flag it with the carrier?

*Return request:*
> Of course — I want you to be happy with your purchase. [Platform policy]. I'll process your refund within [X] days of receiving the return.

### 4. Confirm and send

Always show the draft before sending:
```
Draft reply to [buyer] on [platform]:
---
[reply text]
---
Send? (yes / edit / skip)
```

Only send after explicit user confirmation. Never auto-send.

## Shop Config

```yaml
# ~/.customer-service/shop_config.yaml
shops:
  - platform: etsy
    shop_name: "Lumère"
    tone: "warm, quiet confidence"
    shipping_days_international: 14-21
    return_policy: "30-day returns, buyer pays return shipping"

  - platform: amazon
    shop_name: "Lumère Home"
    tone: "professional, helpful"
    fulfillment: FBM
    return_policy: "Amazon standard return policy"

  - platform: shopify
    shop_url: "lumere.myshopify.com"
    access_token: ""  # leave blank, store in env
    tone: "warm, quiet confidence"
```

## Output per message

```
## 💬 Customer Service — [Platform]

### message
From: [buyer name]
Platform: [etsy / amazon / shopify]
Type: [classified type]
Priority: [high / normal]
Content: [message excerpt]

### draft reply
[3–5 sentences in brand voice]

### action
[send / escalate / flag / skip — with reason]
```

Workflow is complete when all unread messages have a classified type and draft reply,
and user has confirmed or skipped each one.
