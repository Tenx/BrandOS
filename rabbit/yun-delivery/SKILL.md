---
name: yun-delivery
description: >
  Use when the user wants to ship, fulfill, or process Etsy orders via YunExpress (云途).
  Triggers: "帮我发货", "处理订单", "发一下", "有新订单", "submit waybill", "ship orders",
  "云途", "YunExpress", "运单", "待发货", or any mention of fulfilling / shipping Etsy orders.
---

# Yun Delivery

Ship open Etsy orders to YunExpress. Every run is a **fulfillment loop**: list → confirm → submit → record.

Scripts live in your fulfillment directory (e.g. `~/etsy-fulfillment/`).
Run all commands from that directory.

## Steps

**1. List open orders**

```bash
cd ~/etsy-fulfillment
python3 fulfill.py --list
```

Completion: every open receipt shown with receipt ID, buyer name, country, item count.

---

**2. Dry-run each order**

```bash
python3 fulfill.py --dry-run [--receipt-id <id>]
```

Read the printed payload: country, address, weight, declared value, `ShippingMethodCode`.
Verify the route is correct — see [ROUTES.md](ROUTES.md) if unsure which code applies.

Completion: payload looks correct; shipping route and weight are plausible.

---

**3. Submit**

Single order:
```bash
python3 fulfill.py --submit --receipt-id <id>
```

All orders at once (still prompts per order):
```bash
python3 fulfill.py --submit --all
```

On success the script prints the YunExpress waybill number (YT…) and tracking number.

Completion: every order either printed `✓ 运单创建成功!` with a waybill number, or printed a clear error message.

---

**4. Record and report**

Results are appended automatically to `fulfillment/shipment_log.jsonl`.

If any order errored, check the message and resubmit with `--receipt-id` once fixed.

Completion: `shipment_log.jsonl` contains an entry for every order attempted this run.

---

## Quick reference

**Override shipping method** (single run):
```bash
python3 fulfill.py --submit --receipt-id <id> --method THPHR
```

**Query available routes** for a country:
```bash
python3 fulfill.py --list-methods --country US
```

**Track a waybill**:
```bash
python3 fulfill.py --track --order-no HAZUMI-<receipt_id>
# or
python3 fulfill.py --track --order-no YT<waybill_number>
```

**Shipping routes** → [ROUTES.md](ROUTES.md)

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "rabbit": {
    "yun_delivery": {
      "orders_shipped": 0,
      "waybill_numbers": ["waybill1", "waybill2"],
      "carrier": "YunExpress",
      "shipped_at": "YYYY-MM-DD"
    }
  }
}
```
