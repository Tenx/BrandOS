#!/usr/bin/env python3
"""Etsy listing optimizer driven by an etsy_shop_profile.yaml profile."""

import sys
import json
import requests
from pathlib import Path

from etsy_profile import api_credentials, consume_profile_arg, load_profile, project_path

PROFILE = load_profile(consume_profile_arg(sys.argv))
SHOP = PROFILE.get("shop", {})
API_KEY = None
API_SECRET = None
API_BASE = "https://openapi.etsy.com/v3/application"

# Paths
PROJECT_ROOT = Path(PROFILE["paths"]["project_root"])
TOKEN_FILE = project_path("token_file", profile=PROFILE)


def require_api_credentials():
    global API_KEY, API_SECRET
    if not API_KEY or not API_SECRET:
        API_KEY, API_SECRET = api_credentials(PROFILE)
    return API_KEY, API_SECRET


def api_headers(access_token, *, json_body=False):
    api_key, api_secret = require_api_credentials()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'x-api-key': f'{api_key}:{api_secret}'
    }
    if json_body:
        headers['Content-Type'] = 'application/json'
    return headers


def get_access_token():
    """Get access token"""
    if not TOKEN_FILE.exists():
        print("❌ No token found. Please authorize first.")
        sys.exit(1)
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    return token_data['access_token']


def get_listing_details(access_token, listing_id):
    """Fetch listing details"""
    headers = api_headers(access_token)
    response = requests.get(f'{API_BASE}/listings/{listing_id}', headers=headers)
    return response.json() if response.status_code == 200 else None


def detect_missing_tags(title, current_tags):
    """Detect high-value tags missing from listing"""
    title_lower = title.lower()
    all_tags = set([tag.lower() for tag in current_tags])

    suggested_tags = []

    # High-value keywords to check
    opportunities = {
        'boho': ['boho', 'bohemian'],
        'festival': ['festival', 'rave', 'concert'],
        'summer': ['summer', 'beach'],
        'vintage': ['vintage', 'retro'],
        'romantic': ['romantic', 'feminine'],
        'statement': ['statement', 'unique'],
        'artisan': ['artisan', 'crafted'],
        'custom': ['custom', 'personalized']
    }

    for tag, keywords in opportunities.items():
        # If keyword is in title but tag not used
        if any(kw in title_lower for kw in keywords):
            if tag not in all_tags and tag not in [t.lower() for t in current_tags]:
                suggested_tags.append(tag)

    # Additional opportunities based on product type
    if 'mesh' in title_lower and 'fishnet' not in all_tags:
        suggested_tags.append('fishnet')
    if 'rose' in title_lower and 'floral' not in all_tags:
        suggested_tags.append('floral')
    if 'hand' in title_lower:
        if 'handcrafted' not in all_tags:
            suggested_tags.append('handcrafted')

    return suggested_tags[:5]  # Top 5 suggestions


def detect_missing_attributes(listing, inventory):
    """Detect missing attributes that should be set"""
    title = listing.get('title', '').lower()
    missing = []

    # Common attributes to check
    attribute_checks = {
        'neckline': ['off shoulder', 'off-shoulder', 'boat neck', 'v-neck', 'crew neck'],
        'pattern': ['floral', 'rose', 'embellished', 'cable', 'ribbed'],
        'style': ['boho', 'bohemian', 'romantic', 'casual', 'vintage'],
        'occasion': ['festival', 'party', 'casual', 'special'],
        'fit': ['oversized', 'fitted', 'relaxed', 'loose']
    }

    for attr_name, keywords in attribute_checks.items():
        if any(kw in title for kw in keywords):
            missing.append({
                'attribute': attr_name,
                'detected_value': next((kw for kw in keywords if kw in title), None),
                'reason': f'Detected from title'
            })

    return missing


def optimize_price(listing_price, market_data):
    """Suggest price optimization based on market data"""
    suggestions = []

    if market_data and 'median' in market_data:
        median = market_data['median']
        diff_percent = ((listing_price - median) / median) * 100

        if diff_percent > 50:
            suggestions.append({
                'type': 'price_reduction',
                'current': listing_price,
                'suggested': median * 1.25,  # 25% above median
                'reason': f'Current price is {diff_percent:.0f}% above market median'
            })
        elif diff_percent < -20:
            suggestions.append({
                'type': 'price_increase',
                'current': listing_price,
                'suggested': median * 0.9,  # 10% below median
                'reason': 'Pricing below market - potential revenue opportunity'
            })

    return suggestions


def apply_tag_optimization(access_token, shop_id, listing_id, current_tags, new_tags):
    """Add recommended tags to listing"""
    print(f"\n🏷️  Optimizing tags...")

    # Combine current and new tags (max 13)
    all_tags = current_tags[:]
    added = []

    for tag in new_tags:
        if len(all_tags) < 13 and tag not in all_tags:
            all_tags.append(tag)
            added.append(tag)

    if not added:
        print("   ℹ️  No tags to add (already at max or already present)")
        return False

    # Update listing
    headers = api_headers(access_token, json_body=True)

    response = requests.patch(
        f'{API_BASE}/shops/{shop_id}/listings/{listing_id}',
        headers=headers,
        json={'tags': all_tags}
    )

    if response.status_code == 200:
        print(f"   ✅ Added tags: {', '.join(added)}")
        return True
    else:
        print(f"   ❌ Failed to update tags: {response.status_code}")
        return False


def apply_attribute_optimization(access_token, shop_id, listing_id, missing_attributes):
    """Add missing attributes to listing"""
    print(f"\n🏷️  Optimizing attributes...")

    if not missing_attributes:
        print("   ℹ️  No missing attributes detected")
        return False

    headers = api_headers(access_token, json_body=True)

    # Attribute mappings (simplified - would need full property IDs)
    attribute_updates = []

    for attr in missing_attributes[:3]:  # Apply top 3
        print(f"   💡 Detected: {attr['attribute']} = {attr['detected_value']}")

    # Note: Full implementation would map to Etsy property IDs
    print("   ℹ️  Attribute optimization prepared (manual review recommended)")
    return False


def apply_price_optimization(access_token, shop_id, listing_id, inventory, price_suggestion):
    """Apply price optimization to all variations"""
    print(f"\n💰 Price Optimization...")

    if not price_suggestion:
        print("   ℹ️  No price adjustments recommended")
        return False

    suggestion = price_suggestion[0]
    current = suggestion['current']
    suggested = suggestion['suggested']

    print(f"   Current: ${current:.2f}")
    print(f"   Suggested: ${suggested:.2f}")
    print(f"   Reason: {suggestion['reason']}")

    # Would need to update inventory pricing here
    print("   ℹ️  Price optimization prepared (manual review recommended)")
    return False


def generate_optimization_report(listing_id, optimizations):
    """Generate optimization report"""
    report = []
    report.append("🔧 LISTING OPTIMIZATION REPORT")
    report.append("=" * 60)
    report.append(f"Listing ID: {listing_id}")
    report.append(f"URL: https://www.etsy.com/listing/{listing_id}")
    report.append("")

    # Summary
    total_optimizations = sum(len(opts) for opts in optimizations.values())
    applied = sum(1 for opts in optimizations.values() if opts.get('applied'))

    report.append(f"📊 OPTIMIZATION SUMMARY")
    report.append("=" * 60)
    report.append(f"Opportunities found: {total_optimizations}")
    report.append(f"Applied automatically: {applied}")
    report.append("")

    # Tags
    if optimizations.get('tags'):
        report.append("🏷️  TAG OPTIMIZATION")
        report.append("-" * 60)
        tags = optimizations['tags']
        if tags.get('suggested'):
            report.append(f"Suggested tags: {', '.join(tags['suggested'])}")
        if tags.get('applied'):
            report.append("✅ Tags added automatically")
        report.append("")

    # Attributes
    if optimizations.get('attributes'):
        report.append("🏷️  ATTRIBUTE OPTIMIZATION")
        report.append("-" * 60)
        attrs = optimizations['attributes']
        for attr in attrs.get('missing', []):
            report.append(f"• {attr['attribute']}: {attr['detected_value']}")
        report.append("")

    # Pricing
    if optimizations.get('pricing'):
        report.append("💰 PRICING OPTIMIZATION")
        report.append("-" * 60)
        pricing = optimizations['pricing']
        for suggestion in pricing.get('suggestions', []):
            report.append(f"Current: ${suggestion['current']:.2f}")
            report.append(f"Suggested: ${suggestion['suggested']:.2f}")
            report.append(f"Reason: {suggestion['reason']}")
        report.append("")

    report.append("=" * 60)

    return "\n".join(report)


def optimize_listing(listing_id, auto_apply=False, price_data=None):
    """Main optimization function"""
    print(f"\n🔧 Optimizing listing: {listing_id}")
    print("=" * 60)

    access_token = get_access_token()

    # Fetch listing
    print("📥 Analyzing listing...")
    listing = get_listing_details(access_token, listing_id)
    if not listing:
        print("❌ Failed to fetch listing")
        return

    shop_id = SHOP.get("shop_id")
    if not shop_id:
        print("❌ Missing shop.shop_id in etsy_shop_profile.yaml")
        return
    title = listing.get('title', '')
    current_tags = listing.get('tags', [])

    print(f"✅ Listing: {title[:50]}...")
    print("")

    # Detect optimization opportunities
    optimizations = {}

    # 1. Tags
    suggested_tags = detect_missing_tags(title, current_tags)
    if suggested_tags:
        print(f"💡 Found {len(suggested_tags)} tag opportunities: {', '.join(suggested_tags)}")
        optimizations['tags'] = {
            'suggested': suggested_tags,
            'current_count': len(current_tags)
        }

    # 2. Attributes
    missing_attrs = detect_missing_attributes(listing, None)
    if missing_attrs:
        print(f"💡 Found {len(missing_attrs)} missing attributes")
        optimizations['attributes'] = {
            'missing': missing_attrs
        }

    # 3. Pricing
    if price_data:
        listing_price = listing.get('price', {}).get('amount', 0) / listing.get('price', {}).get('divisor', 1)
        price_suggestions = optimize_price(listing_price, price_data)
        if price_suggestions:
            optimizations['pricing'] = {
                'suggestions': price_suggestions
            }

    print("")

    # Apply optimizations
    if auto_apply:
        print("🚀 Applying optimizations automatically...")

        if 'tags' in optimizations:
            applied = apply_tag_optimization(
                access_token, shop_id, listing_id,
                current_tags, optimizations['tags']['suggested']
            )
            optimizations['tags']['applied'] = applied

        if 'attributes' in optimizations:
            applied = apply_attribute_optimization(
                access_token, shop_id, listing_id,
                optimizations['attributes']['missing']
            )
            optimizations['attributes']['applied'] = applied

        if 'pricing' in optimizations:
            applied = apply_price_optimization(
                access_token, shop_id, listing_id, None,
                optimizations['pricing']['suggestions']
            )
            optimizations['pricing']['applied'] = applied
    else:
        print("ℹ️  Manual review mode - no changes applied")
        print("   Use --auto-apply to apply optimizations automatically")

    print("")

    # Generate report
    report = generate_optimization_report(listing_id, optimizations)
    print(report)

    return optimizations


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Optimize Etsy listings from a shop profile')
    parser.add_argument('--listing-id', '-l', type=int, required=True, help='Etsy listing ID')
    parser.add_argument('--auto-apply', '-a', action='store_true', help='Automatically apply optimizations')
    parser.add_argument('--price-data', '-p', type=str, help='Market price data JSON')

    args = parser.parse_args()

    price_data = None
    if args.price_data:
        try:
            price_data = json.loads(args.price_data)
        except:
            print("⚠️  Invalid price data JSON")

    optimize_listing(args.listing_id, args.auto_apply, price_data)
