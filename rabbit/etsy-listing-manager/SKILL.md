---
name: etsy-listing-manager
description: End-to-end Etsy listing management for one or more shops. Use when the user wants Etsy listing SEO copy, titles, descriptions, tags, material tags, attributes, listing QA, CSV audits, marketplace checks, draft publishing, OAuth, image upload, inventory/variations, draft verification, or safe fixes.
---

# Etsy Listing Manager

Use this single skill for Etsy listing work. It consolidates listing writing, QA/auditing, draft publishing, and verify/fix.

## Modes

- `write`: Create Etsy-ready title, description, 13 tags, material tags, and attributes.
- `audit`: Review a single listing, draft, copied listing text, screenshot, URL, or CSV export.
- `publish`: Create or update Etsy draft listings, upload images, set variations, taxonomy, sections, and attributes.
- `verify-fix`: Fetch a draft/listing by ID, verify it, dry-run fixes, then apply safe fixes only when requested.

## Shop Profile

For shop-specific actions, always read a shop profile first. A profile carries shop ID, token path, project paths, shipping profile, readiness state, taxonomy/section rules, variation rules, and safe-fix defaults.

Read `references/shop-profile-schema.md` when creating or editing a profile.

## Writing Listings

Use `references/listing-quality.md`.

Default output sections:

```text
## TITLE
## DESCRIPTION
## TAGS
## MATERIAL TAGS
## ATTRIBUTES
```

Do not invent measurements, materials, certifications, shipping guarantees, delivery dates, or policy terms.

## Auditing Listings

For CSV exports, run the bundled script first:

```bash
python3 <skill>/scripts/audit_etsy_listings.py \
  <input.csv> \
  --report-out reports/etsy_listing_audit.md \
  --json-out reports/etsy_listing_audit.json
```

Then read the report/JSON before giving strategic advice.

For single listing QA, use `references/listing-rules.md` and report issues by severity:

- `Blocker`: likely prevents publishing or materially misleads buyers.
- `High`: hurts search, conversion, compliance, or buyer trust.
- `Medium`: should fix before launch.
- `Low`: polish or optional improvement.

## Publishing And Fixing

Use `references/publish-and-fix.md`.

Bundled scripts live in `scripts/` and are shared across projects. Run them from any project that has `etsy_shop_profile.yaml`, or pass `--profile /absolute/path/to/etsy_shop_profile.yaml`.

```bash
python3 <skill>/scripts/publish_to_etsy.py --listing "product keywords" --price 48 --dry-run
python3 <skill>/scripts/publish_to_etsy.py --listing "product keywords" --price 48
python3 <skill>/scripts/publish_to_etsy.py --auth
python3 <skill>/scripts/verify_listing.py --listing-id 1234567890
python3 <skill>/scripts/auto_fix_listing.py --listing-id 1234567890 --dry-run
python3 <skill>/scripts/optimize_listing.py --listing-id 1234567890
```

Safety defaults:

- Prefer draft publishing.
- Require explicit shop/profile selection before writing to Etsy.
- Use dry-run before applying fixes.
- Never hardcode API secrets into skills or profiles; use env var names or existing token/config files.
- Report listing IDs, changed fields, skipped fields, and manual follow-up.

## Project Integration

Project `AGENTS.md` files should route Etsy work to `$etsy-listing-manager` and provide the shop profile path. Keep shop-specific variables in profiles, not in the skill. Project repositories should not keep duplicate copies of these Python scripts; only keep profiles, brand config, token/env files, listing content, image content, and reports.
