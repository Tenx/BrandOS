# Publish And Fix

## Publish Draft

1. Read the shop profile.
2. Parse the listing file sections: title, description, tags, materials, attributes.
3. Validate title and tags before any API calls.
4. Resolve product images from the profile paths.
5. Create an Etsy draft listing.
6. Upload up to 10 images in display order.
7. Apply configured taxonomy, shop section, attributes, and variations.
8. Report the listing ID and any skipped steps.

Shared script:

```bash
python3 scripts/publish_to_etsy.py \
  --profile /path/to/etsy_shop_profile.yaml \
  --listing "product keywords" \
  --price 48 \
  --dry-run
```

Remove `--dry-run` only after reviewing the payload. Use `--auth` to refresh/create the token for the selected profile.

## Verify

Fetch:

- listing details
- inventory/variations
- images

Check:

- title, description, tags, materials
- image count
- section/taxonomy
- variation names, prices, quantities
- size measurements in description when applicable

## Fix

Default to dry-run. Apply only safe, configured fixes:

- description size chart correction when `auto_fix.allow_description_size_chart_fix` is true
- tag additions/replacements only when user approves
- price/inventory changes only when user approves

After applying fixes, re-verify and report changed fields.

## Update Description (Copy Tweaks)

Use `scripts/update_listing_description.py` whenever the user asks to push a copy edit (a new section, a tightened paragraph, an added reassurance line, a typo fix) to a live or draft listing. This script only PATCHes the `description` field; state, title, tags, price, variations, images, taxonomy, and shop section are untouched.

Two modes:

- `--from-file PATH` — replace the entire description with the contents of a file.
- `--anchor-old[-file] / --anchor-new[-file]` — fetch live, find the old block (must match exactly once), substitute, PATCH. Preferred for section-level edits.

Always dry-run first. Apply only after the diff is reviewed:

```bash
python3 <skill>/scripts/update_listing_description.py \
  --listing-id 4501909515 \
  --anchor-old-file /tmp/old.txt --anchor-new-file /tmp/new.txt
# review the printed diff summary, then:
python3 <skill>/scripts/update_listing_description.py \
  --listing-id 4501909515 \
  --anchor-old-file /tmp/old.txt --anchor-new-file /tmp/new.txt \
  --apply
```

### Anchor-Replace SOP

When making in-place section edits to live listings, follow this pattern:

1. Refresh the access token via `publish_to_etsy.get_access_token()` (auto-refresh path). `verify_listing.get_access_token()` does NOT refresh.
2. GET `/v3/application/listings/{id}` and capture the live description verbatim.
3. Define the old anchor block as a multi-line string copied from the live description, not from the local file (Etsy stores some chars as HTML entities like `&#39;` `&quot;` and may strip the markdown wrapper).
4. Assert the old anchor appears exactly once in the live description. Refuse to proceed otherwise.
5. Substitute and report `len(before) -> len(after)`.
6. PATCH `/v3/application/shops/{shop_id}/listings/{id}` with `{"description": new_desc}` only.
7. Re-fetch and confirm: target phrase present, `state` unchanged, length matches expected.
8. Mirror the same edit into the local `listing_seo/*.txt` so future verifier runs and audits stay in sync.

Listing IDs are recorded as the trailing numeric segment of files in `listing_verifier/reports/` (e.g. `cream_crochet_maxi_dress_flora_2026-05-09_4501909515.txt` → `4501909515`).

## Do Not

- Activate draft listings unless explicitly requested.
- Guess shop IDs, shipping profile IDs, readiness IDs, property IDs, or section IDs.
- Apply measurement fixes as universal truth; they are shop profile policy.
