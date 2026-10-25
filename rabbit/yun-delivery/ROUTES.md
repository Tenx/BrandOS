# Shipping Routes

Auto-selected by destination country in `etsy_orders.py`. Override with `--method <CODE>`.

| Code    | Name                                  | Countries          |
|---------|---------------------------------------|--------------------|
| `FZZXR` | YunExpress Clothing Economy           | US, AU + all others |
| `THPHR` | YunExpress Economy (Unrestricted)     | EU + CH (see list) |

**EU country set** (triggers `THPHR`):
DE FR GB NL BE AT CH IT ES SE DK NO FI PL PT CZ HU RO SK SI

> `FZZXR` is also used for **Australia** — it covers US and all non-EU destinations.

To see the full route catalog for any destination:
```bash
python3 fulfill.py --list-methods --country <ISO2>
```

## Declared product name (EName) — compliance rules

YunExpress requires the **3-element rule**: **Material + Use + Specific product name**.

| Good ✓ | Bad ✗ |
|--------|-------|
| `Women's Crochet Cotton Tank Top` | `Handmade Top` |
| `Women's Mohair Knit Hooded Cardigan` | `Clothing` |
| `Women's Woven Wrap Skirt` | `Product` |

Rules:
- One shipment = one type of product. If a package contains different product types, declare them separately in `Parcels[]`.
- No vague terms: "Clothing", "Product", "Accessory", "Goods", etc.
- Must be ASCII-safe (no `é`, `ü`, `ñ` etc.)

The `etsy_orders.py` script auto-maps Etsy listing titles via `_compliant_ename()`. **Always verify the EName in dry-run output matches the actual item.**

### ⚠️ CName (Chinese declared name) MUST match the actual product category (compliance incident NCR2026092300062, 2026-09-23)

YunExpress flagged a shipment **申报不合规** because the Chinese declared name
(`CName`) was hardcoded to `手工针织上衣` ("handmade knit top") regardless of the
actual garment. A **dress** or **cardigan** declared as a "top" violates the rule
that the declaration must match the real goods (材质 + 用途 + 具体产品名称,
and 申报须与实物相符).

**Fixed 2026-09-24:** `_compliant_ename()` now returns a tuple `(ename, cname)`
where the Chinese name is category-matched:

| Category | EName | CName |
|----------|-------|-------|
| dress | `Women's Knit Dress` | 女士针织连衣裙 |
| maxi dress | `Women's Knit Maxi Dress` | 女士针织长连衣裙 |
| cardigan | `Women's Knit Cardigan` | 女士针织开衫 |
| mohair hooded cardigan | `Women's Mohair Knit Hooded Cardigan` | 女士马海毛针织连帽开衫 |
| sweater | `Women's Knit Sweater` | 女士针织毛衣 |
| tank/top | `Women's Knit Tank Top` | 女士针织背心 |
| vest | `Women's Crochet Knit Vest` | 女士钩织针织马甲 |
| wrap skirt | `Women's Woven Wrap Skirt` | 女士梭织半身裹裙 |

Override both when the auto-map guesses wrong: `YUN_ENAME` (English) **and**
`YUN_CNAME` (Chinese). **Verify the dry-run CName matches the real category — a
dress must not declare as 上衣.**

### ⚠️ Multi-item / SET products MUST be split into separate Parcels[] (compliance incident 2026-09-18)

YunExpress rejected a shipment as **申报不合规 (declaration non-compliant)**: a
two-piece set (**cardigan + wide-leg pants**, Etsy #4173268947 Devin, listing
4573139204) was declared under a **single** EName. YunExpress rule:

> 不同的产品需要分开进行申报，不可以使用同一品名进行货物申报
> (Different product TYPES must each be declared separately — you cannot use one
> product name to cover multiple different items.)

**Why the script missed it:** `etsy_orders.py` builds ONE parcel-item per Etsy
*transaction*. A two-piece set is a single Etsy transaction with one title →
`_compliant_ename()` returns one name → the pants get silently dropped from the
declaration.

**Checklist before submitting ANY order:**
1. Read the item title/description. **Is it a set / bundle / "X + Y" / multi-piece?**
   Watch for: `set`, `two-piece`, `2-piece`, `+`, `cardigan + pants`, `top and
   skirt`, `lounge set`, `matching`, etc.
2. If yes → the single auto-generated EName is WRONG. You must declare **each
   distinct garment type as its own item** in `Parcels[]`, e.g.:
   - `Women's Knit Cardigan` **and** `Women's Knit Wide-Leg Pants`
   - `Women's Crochet Top` **and** `Women's Woven Skirt`
   Split the declared value and weight across the two items too.
3. Since `fulfill.py` has no per-item CLI flag, either hand-build the Parcels
   payload (call `yunexpress_client.create_order()` directly with a corrected
   `Parcels` list), or file the set order manually in the YunExpress OMS backend.
4. A single-garment order (one tank, one dress, one cardigan) is fine as-is —
   this only bites multi-TYPE bundles.

## Declared value limits

| Route  | Hard limit per shipment |
|--------|------------------------|
| FZZXR  | < 60 USD               |
| THPHR  | check with YunExpress  |

If the Etsy order value exceeds the route limit, agree on a reduced declared value with the user before submitting. A common safe value for FZZXR orders is **55 USD**.

## Common API error codes

| Code   | Meaning                              | Fix                                      |
|--------|--------------------------------------|------------------------------------------|
| `1001` | Validation error (field or encoding) | Check EName: must follow 3-element rule (Material + Use + Product), be ASCII-safe (no é ü ñ), and not be vague. Also verify `YUN_CUSTOMER_CODE` / `YUN_API_SECRET` |
| `1002` | Order number already exists          | Duplicate receipt — already submitted    |
| `2001` | Invalid shipping method code         | Run `--list-methods` to find valid code  |
| `2003` | Weight out of range                  | Adjust `UnitWeight` in `etsy_orders.py`  |
| `2010` | Required field missing               | Check Receiver fields in dry-run output  |

## Etsy marking — default carrier

Always use **i-parcel (value 308)** as the shipping carrier when marking orders shipped on Etsy.
- Do NOT use "Other" (requires whitelist-verified carrier name text).
- Do NOT use "Not Available" (no tracking number attached).
