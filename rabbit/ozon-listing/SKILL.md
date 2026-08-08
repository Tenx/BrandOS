---
name: ozon-listing
description: >
  Write and publish product listings to Ozon (Russian marketplace). Generates Russian-language
  title, description, attributes, and rich content — then publishes via Ozon Seller API if
  credentials are configured. Falls back to formatted copy for Seller portal manual paste.
  Use when the user wants to list products on Ozon for the Russian market.
  Triggers: "ozon", "ozon上架", "俄罗斯", "发布到ozon", "ozon listing", "ozon产品",
  "ozon publish", "russian marketplace".
---

# Ozon Listing

Write and publish one product to Ozon. With API credentials: creates product via Seller API.
Without credentials: outputs Seller portal paste-ready copy in Russian.

## Input

User provides:
- **Product copy** — paste from `product-copy` skill output, or describe the product
- **Category** — Ozon category path (e.g. "Товары для дома > Свечи и аромалампы")
- **Price** — in RUB (rubles); USD/EUR price accepted, will note conversion needed
- **Brand name** — as registered or intended for Ozon
- **Attributes** — dimensions, weight, material, color, country of origin (China: Китай)

## Language

All listing content must be in **Russian**. If user provides content in English or Chinese:
1. Translate to Russian first
2. Localize — not literal translation; adapt idioms and marketing language for Russian buyers
3. Keep product names / brand names in Latin script where appropriate (e.g. brand names)

## Ozon Copy Rules

**Name** (≤255 chars)
- Format: `[Тип товара] [Бренд] [Ключевая характеристика], [материал/размер]`
- Russian title case
- Include key search terms naturally

**Description** (≤4000 chars, rich text supported)
- Opening: benefit-led hook (2–3 sentences)
- Features: bullet list with `•` character
- Care/use instructions
- Brand story paragraph (optional but recommended for brand recognition)
- Ozon supports basic HTML: `<b>`, `<br>`, `<ul>`, `<li>`

**Short description** (≤250 chars)
- Shown in search results
- Benefit-first, most important feature

**Attributes** — Ozon requires mandatory category-specific attributes:
- Бренд (Brand)
- Страна-изготовитель (Country of manufacture): Китай
- Материал (Material)
- Цвет (Color)
- Вес (Weight in grams)
- Габариты (Dimensions: LxWxH in mm)
- Category-specific attributes vary — ask user to confirm if uncertain

## Category ID Lookup

Ozon `category_id` is a numeric ID — do NOT hardcode guesses. Always resolve it first.

### Method A — API lookup (recommended if credentials configured)

```bash
POST https://api-seller.ozon.ru/v1/description-category/tree
Headers: Client-Id: <id>  Api-Key: <key>
Body: { "language": "RU" }
```

Walk the returned tree to find the matching leaf node. Use that node's `description_category_id`.

### Method B — Seller portal lookup (no API needed)

1. Open https://seller.ozon.ru → Товары и цены → Добавить товар
2. Search for the category by keyword (e.g. "свечи")
3. Hover over the matching category — the numeric ID appears in the URL or tooltip
4. Copy that ID into `category_id`

### Common categories for cross-border handmade sellers (names only — verify IDs via Method A/B)

| Категория (Russian) | Typical products |
|---|---|
| Свечи и аромалампы | Candles, wax melts, oil burners |
| Ароматизаторы для дома | Reed diffusers, room sprays, sachets |
| Одежда → Женская одежда → Топы | Crop tops, tank tops, camisoles |
| Одежда → Женская одежда → Свитеры и кардиганы | Knit / crochet sweaters, cardigans |
| Украшения для дома | Macrame wall art, woven decor |
| Постельное бельё | Linen, cotton bedding sets |
| Украшения → Браслеты | Handmade bracelets |
| Украшения → Серьги | Handmade earrings |
| Сумки → Женские сумки | Tote bags, crochet bags |
| Косметика → Уход за телом | Body scrubs, bath soaks |

**Note:** Ozon restructures its category tree periodically. Always verify IDs via Method A or B
before submitting — never rely on cached or hardcoded IDs.

**Rich content** (Ozon Premium Content)
- Similar to Amazon A+
- Brief: headline banner + 3 feature blocks + lifestyle image descriptions

## Steps

### 1. Translate and write copy

Translate all product-copy inputs to Russian. Write all blocks following Ozon copy rules.
Flag any attributes that are required by Ozon but not provided by user.

### 2. Publish via Seller API (if credentials configured)

```bash
# ~/.ozon-listing/config.json
{
  "client_id": "...",
  "api_key": "..."
}
```

Get credentials: Ozon Seller portal → Settings → Seller API

API endpoint: `POST /v2/product/import`

Payload structure:
```json
{
  "items": [{
    "name": "...",
    "offer_id": "SKU-001",
    "category_id": 123456,
    "description": "...",
    "price": "1500",
    "vat": "0",
    "weight": 300,
    "dimension_unit": "mm",
    "height": 90, "depth": 80, "width": 80,
    "images": ["https://..."],
    "attributes": [
      { "id": 85, "values": [{ "value": "Китай" }] }
    ]
  }]
}
```

Note: Ozon requires at least one image URL hosted on a public CDN before product creation.
If no hosted image URL is available, output copy for manual upload in Seller portal.

### 3. Output

```
## 🇷🇺 Ozon Listing — [Product Name]

### name (Russian)
[≤255 chars]

### short description (Russian)
[≤250 chars]

### description (Russian)
[≤4000 chars, rich text]

### attributes
Бренд: [brand]
Страна-изготовитель: Китай
Материал: [material in Russian]
Цвет: [color in Russian]
Вес: [grams]
Габариты: [L×W×H mm]
[additional category attributes]

### rich content brief
Banner: [headline]
Block 1: [icon concept + caption]
Block 2: [icon concept + caption]
Block 3: [icon concept + caption]

### missing attributes
[Any required Ozon attributes not provided — ask user before publishing]

### api result
[Task ID if submitted, or "No credentials — paste into Ozon Seller portal manually"]
```

Report is complete when name, description, short description, and all mandatory attributes
are filled. Flag missing attributes before attempting API publish.

## Output Schema

Fields written to `context.json` after this skill completes:

```json
{
  "rabbit": {
    "ozon": {
      "product_id": "string (if published)",
      "name_ru": "string",
      "category_id": 0,
      "status": "draft | submitted"
    }
  }
}
```
