#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


TITLE_LIMIT = 140
MAX_TAGS = 13
TAG_LIMIT = 20

CATEGORY_KEYWORDS = {
    "crystal_bracelets": [
        "bracelet",
        "crystal",
        "amethyst",
        "rose quartz",
        "citrine",
        "quartz",
        "gemstone",
        "beaded bracelet",
    ],
    "sweaters_cardigans": [
        "sweater",
        "cardigan",
        "turtleneck",
        "jumper",
        "pullover",
        "hooded cardigan",
    ],
    "crochet_clothing": [
        "crochet",
        "halter top",
        "tank top",
        "dress",
        "mesh top",
        "fishnet",
        "crop top",
    ],
    "jewelry": ["necklace", "ring", "earrings", "pendant", "jewelry", "jewellery"],
    "home_decor": ["candle", "print", "poster", "vase", "wall art", "decor"],
}

CLAIM_RISK_TERMS = [
    "cure",
    "healing",
    "heal disease",
    "anxiety cure",
    "depression cure",
    "guaranteed luck",
    "100% effective",
]

COMMON_TYPO_TAGS = {
    "hunky_knit": "chunky_knit",
    "hunky knit": "chunky knit",
}


def clean(value):
    return (value or "").strip()


def split_tags(value):
    return [tag.strip() for tag in clean(value).split(",") if tag.strip()]


def combined_text(row):
    return " ".join(
        [
            clean(row.get("TITLE")),
            clean(row.get("TAGS")),
            clean(row.get("DESCRIPTION")),
            clean(row.get("MATERIALS")),
        ]
    ).lower()


def infer_category(row):
    title = clean(row.get("TITLE")).lower()
    text = combined_text(row)

    if any(term in text for term in CATEGORY_KEYWORDS["crystal_bracelets"]):
        return "crystal_bracelets"

    if any(term in title for term in ["dress", "tank top", "halter top", "mesh top", "fishnet", "crop top"]):
        return "crochet_clothing"

    if any(term in text for term in CATEGORY_KEYWORDS["sweaters_cardigans"]):
        return "sweaters_cardigans"

    for category, terms in CATEGORY_KEYWORDS.items():
        if category in {"crystal_bracelets", "sweaters_cardigans"}:
            continue
        if any(term in text for term in terms):
            return category

    return "other"


def price_number(row):
    try:
        return float(clean(row.get("PRICE")))
    except ValueError:
        return None


def listing_issues(row):
    title = clean(row.get("TITLE"))
    tags = split_tags(row.get("TAGS"))
    tag_set = {tag.lower() for tag in tags}
    materials = clean(row.get("MATERIALS"))
    category = infer_category(row)
    text = combined_text(row)

    issues = []

    if not title:
        issues.append({"code": "missing_title", "detail": "TITLE is empty"})
    elif len(title) > TITLE_LIMIT:
        issues.append({"code": "title_too_long", "detail": f"{len(title)} characters"})

    if len(tags) > MAX_TAGS:
        issues.append({"code": "too_many_tags", "detail": f"{len(tags)} tags"})
    elif len(tags) < MAX_TAGS:
        issues.append({"code": "unused_tag_slots", "detail": f"{len(tags)} of {MAX_TAGS} tags used"})

    long_tags = [tag for tag in tags if len(tag) > TAG_LIMIT]
    if long_tags:
        issues.append({"code": "tag_too_long", "detail": ", ".join(long_tags)})

    if not materials:
        issues.append({"code": "missing_materials", "detail": "MATERIALS is empty"})

    for typo, suggestion in COMMON_TYPO_TAGS.items():
        if typo in tag_set:
            issues.append({"code": "tag_typo", "detail": f"{typo} -> {suggestion}"})

    if category in {"crystal_bracelets", "jewelry"}:
        risky = [term for term in CLAIM_RISK_TERMS if term in text]
        if risky:
            issues.append({"code": "claim_risk", "detail": ", ".join(risky)})

    return issues


def load_rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def price_summary(rows):
    prices = [price_number(row) for row in rows]
    prices = [price for price in prices if price is not None]
    if not prices:
        return {"min": None, "max": None, "average": None}
    return {
        "min": round(min(prices), 2),
        "max": round(max(prices), 2),
        "average": round(sum(prices) / len(prices), 2),
    }


def analyze(rows, focus_categories):
    listings = []
    category_rows = defaultdict(list)
    tag_counter = Counter()
    issue_counter = Counter()

    for index, row in enumerate(rows, 1):
        tags = split_tags(row.get("TAGS"))
        category = infer_category(row)
        issues = listing_issues(row)
        category_rows[category].append(row)
        tag_counter.update(tag.lower() for tag in tags)
        issue_counter.update(issue["code"] for issue in issues)
        listings.append(
            {
                "index": index,
                "title": clean(row.get("TITLE")),
                "sku": clean(row.get("SKU")),
                "category": category,
                "price": clean(row.get("PRICE")),
                "currency": clean(row.get("CURRENCY_CODE")),
                "quantity": clean(row.get("QUANTITY")),
                "tag_count": len(tags),
                "materials": clean(row.get("MATERIALS")),
                "issues": issues,
            }
        )

    categories = {category: len(items) for category, items in sorted(category_rows.items())}
    missing_focus = [category for category in focus_categories if categories.get(category, 0) == 0]

    return {
        "listing_count": len(rows),
        "categories": categories,
        "focus_categories": focus_categories,
        "missing_focus_categories": missing_focus,
        "issue_counts": dict(issue_counter),
        "price_summary": price_summary(rows),
        "category_price_summary": {
            category: price_summary(items) for category, items in sorted(category_rows.items())
        },
        "repeated_tags_top_15": tag_counter.most_common(15),
        "listings": listings,
    }


def issue_label(code):
    labels = {
        "missing_title": "标题缺失",
        "title_too_long": "标题超过 140 字符",
        "too_many_tags": "Tags 超过 13 个",
        "unused_tag_slots": "Tags 未用满",
        "tag_too_long": "Tag 超过 20 字符",
        "missing_materials": "Materials 缺失",
        "tag_typo": "Tag 拼写错误",
        "claim_risk": "水晶/珠宝合规风险",
    }
    return labels.get(code, code)


def render_markdown(result):
    price = result["price_summary"]
    lines = [
        "# Etsy Listing 体检报告",
        "",
        "## 数据概览",
        "",
        "| 指标 | 结果 |",
        "| --- | --- |",
        f"| Listing 总数 | {result['listing_count']} |",
        f"| 价格区间 | {price['min']}-{price['max']} |",
        f"| 平均价格 | {price['average']} |",
        "",
        "## 品类结构",
        "",
        "| 品类 | 数量 |",
        "| --- | ---: |",
    ]

    for category, count in result["categories"].items():
        lines.append(f"| {category} | {count} |")

    if result["missing_focus_categories"]:
        lines.extend(["", "## 品类缺口", ""])
        for category in result["missing_focus_categories"]:
            lines.append(f"- `{category}` 当前为 0，需要补 Listing 或确认该项目不做此品类。")

    lines.extend(["", "## 最优先动作", ""])
    if result["issue_counts"]:
        for code, count in sorted(result["issue_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {issue_label(code)}：{count}")
    else:
        lines.append("- 没有发现硬性字段或 Etsy 限制问题。")

    lines.extend(["", "## 每个 Listing 的问题与动作", ""])
    for item in result["listings"]:
        lines.extend(
            [
                f"### {item['index']}. {item['title']}",
                "",
                f"- 品类：{item['category']}",
                f"- 价格：{item['price']} {item['currency']}",
                f"- Tags：{item['tag_count']}/13",
                f"- Materials：{item['materials'] or '缺失'}",
            ]
        )
        if item["issues"]:
            for issue in item["issues"]:
                lines.append(f"- 问题：{issue_label(issue['code'])}（{issue['detail']}）")
        else:
            lines.append("- 问题：无硬性问题")
        lines.append("")

    lines.extend(
        [
            "## Tags 观察",
            "",
            "| Tag | 出现次数 |",
            "| --- | ---: |",
        ]
    )
    for tag, count in result["repeated_tags_top_15"]:
        lines.append(f"| {tag} | {count} |")

    lines.extend(
        [
            "",
            "## 下一步 action",
            "",
            "1. 先修复 `最优先动作` 中的硬性问题。",
            "2. 再按品类拆分标题和 tags 策略，不要把所有 listing 用同一组泛词。",
            "3. 下载 Orders CSV 或 Ads/Search terms 数据后，把 listing 质量和真实表现合并分析。",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--focus-categories", default="")
    parser.add_argument("--json-out")
    parser.add_argument("--report-out")
    args = parser.parse_args()

    focus_categories = [item.strip() for item in args.focus_categories.split(",") if item.strip()]
    result = analyze(load_rows(args.csv_path), focus_categories)

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.report_out:
        Path(args.report_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_out).write_text(render_markdown(result), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
