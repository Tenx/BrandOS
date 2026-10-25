---
name: yun-delivery
description: >
  Use when the user wants to ship, fulfill, or process Etsy orders via YunExpress (云途).
  Triggers: "帮我发货", "处理订单", "发一下", "有新订单", "submit waybill", "ship orders",
  "云途", "YunExpress", "运单", "待发货", or any mention of fulfilling / shipping Hazumi orders.
---

Ship open Etsy orders to YunExpress. Every run is a **fulfillment loop**: list → confirm → submit → label → mark shipped on Etsy.

Scripts live in `/Users/I742076/.claude/projects/hazumi/fulfillment/`.
Run all commands from that directory.

## Steps

**1. List open orders**

```bash
cd /Users/I742076/.claude/projects/hazumi/fulfillment
python3 fulfill.py --list
```

Completion: every open receipt shown with receipt ID, buyer name, country, item count.

---

**2. Dry-run each order**

```bash
python3 fulfill.py --dry-run [--receipt-id <id>]
```

Read the printed payload carefully:

- **Country / ShippingMethodCode**: see [ROUTES.md](ROUTES.md) for which code to use per destination.
- **Weight**: default 0.4 kg/item — adjust if the actual item is heavier (e.g. knitwear 0.6–0.9 kg).
- **Declared value (UnitPrice × Quantity)**: FZZXR route hard limit is **< 60 USD**. If Etsy order value exceeds this, you must reduce the declared value manually. Discuss with user before changing — agree on a value (e.g. 55 USD) before submitting.
- **EName (declared product name)**: must follow the **3-element rule: Material + Use + Product Name** (e.g. `Women's Crochet Cotton Tank Top`). The script auto-maps Etsy titles via `_compliant_ename()` in `etsy_orders.py` — verify the output matches the actual item. Must also be ASCII-safe; non-ASCII chars (`é`, `ü`, `ñ`) cause a `1001` error.

Completion: payload looks correct; route, weight, and declared value are all plausible.

---

**3. Submit**

Single order:
```bash
echo "y" | python3 fulfill.py --submit --receipt-id <id>
```

> Note: `fulfill.py --submit` uses `input()` for confirmation. Pipe `echo "y"` or the script will hang waiting for stdin.

All orders at once:
```bash
python3 fulfill.py --submit --all
```
(Still prompts per order — requires interactive terminal.)

On success the script prints the YunExpress waybill number (`YT…`). **Tracking number may be null at this point** — it is assigned later by the carrier.

Completion: every order either printed `✓ 运单创建成功!` with a waybill number, or a clear error message.

---

**4. Download the shipping label**

The label PDF URL comes from the `print_label` API. The current `print_label()` function uses GET but the endpoint requires POST with an array. Call directly:

```python
import yunexpress_client as yun
resp = yun._post('/api/Label/Print', ['YT...waybill...'])
url = (resp.get('Item') or [{}])[0].get('Url', '')
print(url)
```

Then download:
```bash
curl -L "<url>" -o ~/Downloads/label_YT<waybill>.pdf
open ~/Downloads/label_YT<waybill>.pdf
```

Completion: PDF saved to `~/Downloads/`, user can print it.

---

**5. Wait for tracking number, then mark shipped on Etsy**

Tracking numbers are assigned by the carrier after label is printed — usually within a few hours to 1 business day. Check with:

```bash
python3 fulfill.py --track --order-no YT<waybill>
```

Once a tracking number appears, mark the order shipped on Etsy via opencli:

- Navigate to `https://www.etsy.com/your/orders/sold?status=paid`
- Tick the order checkbox → click **Complete order** (toolbar button `button.btn.btn-secondary`, not the shadow-DOM `clg-icon-button`)
- In the modal, set **Shipping carrier = i-parcel** (value `308`) — this is the default carrier for Hazumi
- Enter the tracking number using `document.execCommand('insertText')` (React inputs require this; direct `.value =` assignment is silently ignored)
- Submit

> **Do NOT mark as shipped before the tracking number is available.** Selecting "Not Available" leaves the order without a tracking number and is harder to fix retroactively.

Completion: order shows "Pre-transit" or similar on Etsy; receipt confirmed shipped.

---

**6. Pickup scheduling (揽收预约)**

The YunExpress OMS API has **no pickup scheduling endpoint** (all known paths return 404). Schedule pickups manually through the YunExpress web backend (`oms.yunexpress.com`) or by contacting YunExpress customer service directly.

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
