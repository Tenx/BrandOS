#!/usr/bin/env python3
"""
Etsy Market Scout
=================
Search Etsy listings for a keyword and return pricing, review volume,
and competition density — the three signals that matter for niche entry.

Usage:
    python3 etsy_scout.py "crochet top"
    python3 etsy_scout.py "crochet top" --limit 20
    python3 etsy_scout.py "crochet top" --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

def find_token() -> str:
    """Look for an Etsy OAuth token in the standard etsy-listing-manager location."""
    candidates = [
        Path.home() / ".etsy" / "token.json",
        Path.home() / ".agents" / "skills" / "etsy-listing-manager" / "token.json",
        Path.home() / ".claude" / "skills" / "etsy-listing-manager" / "token.json",
    ]
    for p in candidates:
        if p.exists():
            data = json.loads(p.read_text())
            token = data.get("access_token") or data.get("token")
            if token:
                return token

    token = os.environ.get("ETSY_ACCESS_TOKEN", "")
    if token:
        return token

    print("❌ No Etsy token found.")
    print("   Run OAuth setup from rabbit/etsy-listing-manager first, or set ETSY_ACCESS_TOKEN.")
    sys.exit(1)


# ── Etsy API ──────────────────────────────────────────────────────────────────

def search_listings(keyword: str, limit: int, token: str) -> list[dict]:
    try:
        import requests
    except ImportError:
        print("❌ Missing dependency: pip3 install requests")
        sys.exit(1)

    url = "https://openapi.etsy.com/v3/application/listings/active"
    headers = {
        "x-api-key": token,
        "Accept": "application/json",
    }
    params = {
        "keywords": keyword,
        "limit": min(limit, 100),
        "sort_on": "score",
        "sort_order": "desc",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    if resp.status_code == 401:
        print("❌ Etsy token expired or invalid. Re-run OAuth setup.")
        sys.exit(1)
    if resp.status_code != 200:
        print(f"❌ Etsy API error {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)

    return resp.json().get("results", [])


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze(listings: list[dict], keyword: str) -> None:
    if not listings:
        print(f"No Etsy listings found for '{keyword}'.")
        return

    prices = [l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 1), 1)
              for l in listings if l.get("price")]
    reviews = [l.get("num_favorers", 0) for l in listings]
    titles = [l.get("title", "") for l in listings[:5]]

    price_min = min(prices) if prices else 0
    price_max = max(prices) if prices else 0
    price_avg = sum(prices) / len(prices) if prices else 0
    review_top = max(reviews) if reviews else 0
    review_avg = sum(reviews) / len(reviews) if reviews else 0

    print(f"\n=== Etsy Scout — {keyword} ===")
    print(f"Listings found : {len(listings)}")
    print(f"Price range    : ${price_min:.0f} – ${price_max:.0f}  (avg ${price_avg:.0f})")
    print(f"Top favorites  : {review_top}  (avg {review_avg:.0f})")
    print(f"\nTop 5 listing titles:")
    for i, title in enumerate(titles, 1):
        print(f"  {i}. {title}")

    # Competition density signal
    if len(listings) >= 50 and review_avg < 20:
        signal = "HIGH competition, LOW engagement — hard to break in without a strong angle"
    elif review_avg > 100:
        signal = "VALIDATED demand — buyers are active, worth entering with differentiated product"
    elif review_avg > 30:
        signal = "MODERATE demand — viable if you have a clear style advantage"
    else:
        signal = "LOW signal — niche may be too new or too small"

    print(f"\nEtsy signal: {signal}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Etsy Market Scout")
    parser.add_argument("keyword", help="Product category keyword")
    parser.add_argument("--limit", type=int, default=50, help="Number of listings to fetch (max 100)")
    parser.add_argument("--dry-run", action="store_true", help="Preview query without calling API")
    args = parser.parse_args()

    print(f"🐕 Scouting Etsy: '{args.keyword}'")

    if args.dry_run:
        print(f"   [dry-run] Would search Etsy for '{args.keyword}', limit={args.limit}")
        return

    token = find_token()
    listings = search_listings(args.keyword, args.limit, token)
    analyze(listings, args.keyword)


if __name__ == "__main__":
    main()
