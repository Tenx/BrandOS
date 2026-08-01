#!/usr/bin/env python3
"""
Update an existing Etsy listing's description field.

Two modes:

  1. --from-file PATH        Replace the entire description with the file contents.
  2. --anchor-old / --anchor-new
                              Anchor-replace: fetch the live description, find the
                              old anchor (must appear exactly once), substitute the
                              new text, and PATCH. Safer than full replacement when
                              you only want to tweak a section.

Always dry-runs by default. Pass --apply to actually PATCH the live listing.

Only the `description` field is modified. State, title, tags, price, variations,
images, taxonomy and shop section are untouched. The script will refuse to
activate or deactivate a listing.

Usage examples:

  # Dry-run a full description replace
  python3 update_listing_description.py \
      --listing-id 4501909515 \
      --from-file ./new_description.txt

  # Apply a section-level edit using anchor replace
  python3 update_listing_description.py \
      --listing-id 4501909515 \
      --anchor-old-file ./old_block.txt \
      --anchor-new-file ./new_block.txt \
      --apply
"""

import argparse
import sys
from pathlib import Path

# Reuse the publisher's auto-refresh token logic and API helpers.
sys.path.insert(0, str(Path(__file__).parent))
import publish_to_etsy as p  # noqa: E402
import requests  # noqa: E402


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _diff_summary(before: str, after: str) -> str:
    delta = len(after) - len(before)
    sign = "+" if delta >= 0 else ""
    return f"{len(before)} -> {len(after)} chars ({sign}{delta})"


def _shop_id_from_listing(listing_data: dict) -> int:
    sid = listing_data.get("shop_id")
    if not sid:
        raise SystemExit("❌ Could not determine shop_id from listing payload.")
    return int(sid)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update an Etsy listing description.")
    parser.add_argument("--listing-id", required=True, help="Etsy listing ID")
    parser.add_argument("--from-file", help="Path to file containing the full new description")
    parser.add_argument("--anchor-old", help="Inline old anchor text (must match exactly once)")
    parser.add_argument("--anchor-new", help="Inline new anchor text")
    parser.add_argument("--anchor-old-file", help="File with old anchor text")
    parser.add_argument("--anchor-new-file", help="File with new anchor text")
    parser.add_argument("--apply", action="store_true",
                        help="Actually PATCH the listing. Default is dry-run.")
    args = parser.parse_args()

    have_full = bool(args.from_file)
    have_anchor = bool(
        (args.anchor_old or args.anchor_old_file)
        and (args.anchor_new is not None or args.anchor_new_file)
    )
    if have_full == have_anchor:
        parser.error(
            "Choose exactly one mode: --from-file OR (--anchor-old[-file] + --anchor-new[-file])."
        )

    # Auth (auto-refreshes if expired).
    access_token = p.get_access_token()
    headers = p.api_headers(access_token)
    headers["Content-Type"] = "application/json"

    # Fetch current listing.
    listing_id = args.listing_id
    print(f"📥 Fetching listing {listing_id}...")
    resp = requests.get(f"{p.API_BASE}/listings/{listing_id}", headers=headers, timeout=45)
    if resp.status_code != 200:
        print(f"❌ Fetch failed: {resp.status_code}\n{resp.text[:400]}")
        return 1
    listing = resp.json()
    shop_id = _shop_id_from_listing(listing)
    state = listing.get("state")
    title = listing.get("title", "")
    current_desc = listing.get("description", "")
    print(f"   title: {title[:80]}")
    print(f"   state: {state}")
    print(f"   current desc length: {len(current_desc)}")

    # Build new description.
    if have_full:
        new_desc = _load(Path(args.from_file))
        print(f"   mode: full replace from {args.from_file}")
    else:
        old = _load(Path(args.anchor_old_file)) if args.anchor_old_file else args.anchor_old
        if args.anchor_new_file:
            new = _load(Path(args.anchor_new_file))
        else:
            new = args.anchor_new
        count = current_desc.count(old)
        if count != 1:
            print(f"❌ Anchor must match exactly once. Found {count} matches.")
            return 2
        new_desc = current_desc.replace(old, new)
        print(f"   mode: anchor replace (1 match)")

    print(f"   description: {_diff_summary(current_desc, new_desc)}")

    if new_desc == current_desc:
        print("ℹ️  No-op: description unchanged.")
        return 0

    if not args.apply:
        print("\n🟡 DRY-RUN. Re-run with --apply to PATCH the live listing.")
        return 0

    # PATCH.
    url = f"{p.API_BASE}/shops/{shop_id}/listings/{listing_id}"
    patch = requests.patch(url, headers=headers, json={"description": new_desc}, timeout=45)
    if patch.status_code != 200:
        print(f"❌ PATCH failed: {patch.status_code}\n{patch.text[:400]}")
        return 3
    body = patch.json()
    print(f"✅ PATCH ok. state={body.get('state')} desc_len={len(body.get('description', ''))}")

    # Re-verify state did not flip.
    if body.get("state") != state:
        print(f"⚠️  Listing state changed: {state} -> {body.get('state')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
