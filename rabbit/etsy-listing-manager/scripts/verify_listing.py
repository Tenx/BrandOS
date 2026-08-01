#!/usr/bin/env python3
"""Etsy listing verifier driven by an etsy_shop_profile.yaml profile."""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

from etsy_profile import api_credentials, consume_profile_arg, load_profile, project_path

PROFILE = load_profile(consume_profile_arg(sys.argv))
SHOP = PROFILE.get("shop", {})
VERIFICATION = PROFILE.get("verification", {})
VARIATIONS = PROFILE.get("variations", {})
AUTO_FIX = PROFILE.get("auto_fix", {})
API_KEY = None
API_SECRET = None
API_BASE = "https://openapi.etsy.com/v3/application"

# Paths
PROJECT_ROOT = Path(PROFILE["paths"]["project_root"])
TOKEN_FILE = project_path("token_file", profile=PROFILE)
LISTING_DIR = project_path("listing_dir", profile=PROFILE)
REPORTS_DIR = project_path("reports_dir", profile=PROFILE)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def require_api_credentials():
    global API_KEY, API_SECRET
    if not API_KEY or not API_SECRET:
        API_KEY, API_SECRET = api_credentials(PROFILE)
    return API_KEY, API_SECRET


def api_headers(access_token):
    api_key, api_secret = require_api_credentials()
    return {
        'Authorization': f'Bearer {access_token}',
        'x-api-key': f'{api_key}:{api_secret}'
    }


def should_validate_size_measurements():
    return bool(
        VARIATIONS.get("enabled", False)
        or AUTO_FIX.get("allow_description_size_chart_fix", False)
        or VERIFICATION.get("expected_size_names")
    )


def should_expect_size_variations(title):
    """Mirror publisher rules so one-size/non-apparel listings are not flagged."""
    if not VARIATIONS.get("enabled", True):
        return False
    title_lower = title.lower()
    non_apparel_terms = VARIATIONS.get("skip_if_title_contains", [])
    return not any(term in title_lower for term in non_apparel_terms)


def get_access_token():
    """Get access token from publisher"""
    if not TOKEN_FILE.exists():
        print("❌ No token found. Please authorize first:")
        print("python3 <skill>/scripts/publish_to_etsy.py --auth --profile /path/to/etsy_shop_profile.yaml")
        sys.exit(1)

    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    return token_data['access_token']


def get_listing_details(access_token, listing_id):
    """Fetch listing details from Etsy"""
    headers = api_headers(access_token)

    response = requests.get(
        f'{API_BASE}/listings/{listing_id}',
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch listing: {response.status_code}")
        print(response.text[:200])
        return None


def get_listing_inventory(access_token, listing_id):
    """Fetch inventory/variations"""
    headers = api_headers(access_token)

    response = requests.get(
        f'{API_BASE}/listings/{listing_id}/inventory',
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    return None


def get_listing_images(access_token, listing_id):
    """Fetch listing images"""
    headers = api_headers(access_token)

    response = requests.get(
        f'{API_BASE}/listings/{listing_id}/images',
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    return None


def verify_completeness(listing, inventory, images):
    """Check listing completeness"""
    issues = []
    checks = []

    # Title
    title = listing.get('title', '')
    if title:
        checks.append(f"✅ Title: {title[:50]}... ({len(title)} chars)")
    else:
        issues.append("❌ Missing title")

    # Description
    desc = listing.get('description', '')
    if desc and len(desc) > 100:
        checks.append(f"✅ Description: {len(desc)} characters")
    else:
        issues.append("⚠️  Description too short or missing")

    # Tags
    tags = listing.get('tags', [])
    if len(tags) >= 13:
        checks.append(f"✅ Tags: {len(tags)} tags")
    else:
        issues.append(f"⚠️  Only {len(tags)} tags (13 recommended)")

    # Size variations
    expected_size_names = VERIFICATION.get("expected_size_names", ["Small", "Medium", "Large"])
    if should_expect_size_variations(title) and inventory and 'products' in inventory:
        products = inventory['products']
        sizes = [p['property_values'][0]['values'][0] for p in products if p.get('property_values')]
        if all(size in sizes for size in expected_size_names):
            checks.append(f"✅ Size variations: {', '.join(sizes)}")
        else:
            issues.append(f"⚠️  Size variations found: {', '.join(sizes) or 'none'} (expected: {', '.join(expected_size_names)})")
    elif should_expect_size_variations(title):
        issues.append("⚠️  No size variations found")
    else:
        checks.append("✅ Size variations skipped for one-size/non-apparel title")

    # Images
    min_images = int(VERIFICATION.get("min_images", 4))
    image_count = images.get('count', 0) if images else 0
    if image_count >= min_images:
        checks.append(f"✅ Images: {image_count} uploaded")
    else:
        issues.append(f"⚠️  Only {image_count} images ({min_images}+ recommended)")

    # Shop section
    section_id = listing.get('shop_section_id')
    if section_id:
        checks.append(f"✅ Shop section: {section_id}")
    else:
        issues.append("⚠️  No shop section assigned")

    return checks, issues


def verify_pricing(inventory, base_price):
    """Verify pricing logic"""
    issues = []
    checks = []

    if not inventory or 'products' not in inventory:
        return checks, ["⚠️  No pricing data found"]

    products = inventory['products']
    prices = {}

    for product in products:
        if product.get('property_values'):
            size = product['property_values'][0]['values'][0]
            offering = product['offerings'][0]
            price = offering['price']['amount'] / offering['price']['divisor']
            quantity = offering['quantity']
            prices[size] = {'price': price, 'quantity': quantity}

    single_products = [
        product for product in products
        if not product.get('property_values') and product.get('offerings')
    ]
    if not prices and single_products:
        offering = single_products[0]['offerings'][0]
        price = offering['price']['amount'] / offering['price']['divisor']
        quantity = offering['quantity']
        checks.append(f"✅ Single price: ${price:.2f}")
        checks.append(f"✅ Quantity: {quantity}")
        return checks, issues

    # Check if prices follow $5 increment pattern
    increment = float(VERIFICATION.get("expected_price_increment", 5))
    expected_quantity = int(VERIFICATION.get("expected_quantity_per_variation", 50))
    if 'Small' in prices and 'Medium' in prices and 'Large' in prices:
        s_price = prices['Small']['price']
        m_price = prices['Medium']['price']
        l_price = prices['Large']['price']

        if abs(m_price - s_price - increment) < 0.01 and abs(l_price - m_price - increment) < 0.01:
            checks.append(f"✅ Pricing: S=${s_price:.2f}, M=${m_price:.2f}, L=${l_price:.2f}")
        else:
            issues.append(f"⚠️  Pricing not following ${increment:.0f} increments: S=${s_price:.2f}, M=${m_price:.2f}, L=${l_price:.2f}")

    # Check quantities
    quantities = [p['quantity'] for p in prices.values()]
    if quantities and all(q == expected_quantity for q in quantities):
        checks.append(f"✅ Quantity: {expected_quantity} per size")
    elif quantities:
        issues.append(f"⚠️  Inconsistent quantities: {quantities}")

    return checks, issues


def verify_size_measurements(description, title):
    """
    CRITICAL: Validate size measurements in description
    This is important because measurements are AI-generated and may contain errors
    """
    import re

    issues = []
    checks = []
    warnings = []

    # Extract size chart from description
    size_chart_pattern = r'Size Chart:.*?(?=\n\n|$)'
    size_chart_match = re.search(size_chart_pattern, description, re.DOTALL | re.IGNORECASE)

    if not size_chart_match:
        issues.append("❌ CRITICAL: No size chart found in description")
        return checks, issues, warnings

    size_chart = size_chart_match.group(0)
    checks.append("✅ Size chart present in description")

    # Extract measurements for each size
    measurements = {}

    # Parse S, M, L measurements
    for size in ['S', 'M', 'L']:
        # Pattern: • S: Bust X-Xcm/X-X", ... Length Xcm/X", Sleeve Xcm/X"
        pattern = rf'•\s*{size}:\s*Bust\s*([\d-]+)cm.*?Length\s*([\d]+)cm.*?(?:Sleeve\s*([\d]+)cm)?'
        match = re.search(pattern, size_chart)

        if match:
            bust_range = match.group(1)
            length = int(match.group(2))
            sleeve = int(match.group(3)) if match.group(3) else None

            # Parse bust range (e.g., "100-106" or "80-85")
            if '-' in bust_range:
                bust_min, bust_max = map(int, bust_range.split('-'))
                bust_avg = (bust_min + bust_max) / 2
            else:
                bust_avg = int(bust_range)

            measurements[size] = {
                'bust': bust_avg,
                'length': length,
                'sleeve': sleeve
            }

    if len(measurements) != 3:
        issues.append(f"❌ CRITICAL: Incomplete measurements (found {len(measurements)}/3 sizes)")
        return checks, issues, warnings

    checks.append(f"✅ All size measurements found (S, M, L)")

    # Validate S < M < L progression
    if not (measurements['S']['bust'] < measurements['M']['bust'] < measurements['L']['bust']):
        issues.append("❌ CRITICAL: Bust measurements not in S < M < L order")
    else:
        checks.append("✅ Bust progression S < M < L is correct")

    if not (measurements['S']['length'] < measurements['M']['length'] < measurements['L']['length']):
        warnings.append("⚠️  Length not increasing with size (may be intentional)")

    # Check increment sizes (should be 5-8cm between sizes)
    bust_increment_sm = measurements['M']['bust'] - measurements['S']['bust']
    bust_increment_ml = measurements['L']['bust'] - measurements['M']['bust']

    if 3 < bust_increment_sm < 10 and 3 < bust_increment_ml < 10:
        checks.append(f"✅ Bust increments reasonable: S→M={bust_increment_sm:.0f}cm, M→L={bust_increment_ml:.0f}cm")
    else:
        issues.append(f"❌ CRITICAL: Unusual bust increments: S→M={bust_increment_sm:.0f}cm, M→L={bust_increment_ml:.0f}cm (expected 5-8cm)")

    # Validate measurements are realistic for garment type
    title_lower = title.lower()

    # Determine garment type
    is_oversized = 'oversized' in title_lower or 'chunky' in title_lower
    is_dress = 'dress' in title_lower or 'maxi' in title_lower
    is_top = 'top' in title_lower or 'crop' in title_lower
    is_sweater = 'sweater' in title_lower or 'cardigan' in title_lower or 'jumper' in title_lower

    # Check bust measurements
    avg_bust = measurements['M']['bust']
    if is_oversized:
        if 95 < avg_bust < 135:
            checks.append(f"✅ Bust measurement realistic for oversized ({avg_bust:.0f}cm)")
        else:
            issues.append(f"❌ CRITICAL: Bust {avg_bust:.0f}cm unrealistic for oversized garment")
    elif is_top or is_sweater:
        if 80 < avg_bust < 125:
            checks.append(f"✅ Bust measurement realistic ({avg_bust:.0f}cm)")
        else:
            issues.append(f"❌ CRITICAL: Bust {avg_bust:.0f}cm unrealistic for {title_lower.split()[0]}")

    # Check length measurements
    avg_length = measurements['M']['length']
    if is_dress:
        if 130 < avg_length < 160:
            checks.append(f"✅ Length realistic for maxi dress ({avg_length}cm)")
        elif avg_length < 100:
            issues.append(f"❌ CRITICAL: Length {avg_length}cm too short for maxi dress")
        else:
            warnings.append(f"⚠️  Length {avg_length}cm seems long for maxi dress")
    elif is_top:
        if 35 < avg_length < 75:
            checks.append(f"✅ Length realistic for top ({avg_length}cm)")
        else:
            issues.append(f"❌ CRITICAL: Length {avg_length}cm unrealistic for top")
    elif is_sweater:
        if 55 < avg_length < 85:
            checks.append(f"✅ Length realistic for sweater ({avg_length}cm)")
        else:
            warnings.append(f"⚠️  Length {avg_length}cm unusual for sweater")

    # Check sleeve length if present
    if measurements['M']['sleeve']:
        avg_sleeve = measurements['M']['sleeve']
        if 55 < avg_sleeve < 68:
            checks.append(f"✅ Sleeve length realistic ({avg_sleeve}cm)")
        else:
            warnings.append(f"⚠️  Sleeve length {avg_sleeve}cm unusual (expected 55-65cm)")

    return checks, issues, warnings


def search_etsy_market(title):
    """Search Etsy for similar products and analyze pricing"""
    from urllib.parse import quote

    # Extract key search terms from title
    keywords = []
    title_lower = title.lower()

    # Common product types
    if 'cardigan' in title_lower:
        keywords.append('cardigan')
    if 'sweater' in title_lower or 'jumper' in title_lower:
        keywords.append('sweater')
    if 'mesh' in title_lower or 'fishnet' in title_lower:
        keywords.append('mesh')
    if 'crochet' in title_lower:
        keywords.append('crochet')
    if 'knit' in title_lower:
        keywords.append('knit')

    # Modifiers
    if 'hand' in title_lower:
        keywords.append('handmade')
    if 'rose' in title_lower or 'floral' in title_lower:
        keywords.append('floral')

    search_query = ' '.join(keywords[:4]) if keywords else title[:30]

    return {
        'search_query': search_query,
        'keywords_used': keywords,
        'note': 'Market data placeholder - ready for WebSearch MCP integration'
    }


def search_market_with_websearch(title):
    """Search for similar products using WebSearch MCP"""
    # This function will use the WebSearch tool when called from Claude
    # For now, return instructions for Claude to use WebSearch

    keywords = []
    title_lower = title.lower()

    # Extract product type
    product_type = None
    if 'cardigan' in title_lower:
        product_type = 'cardigan'
    elif 'sweater' in title_lower or 'jumper' in title_lower:
        product_type = 'sweater'
    elif 'top' in title_lower:
        product_type = 'top'
    elif 'mesh' in title_lower or 'fishnet' in title_lower:
        product_type = 'mesh top'

    # Extract materials
    materials = []
    if 'crochet' in title_lower or 'knit' in title_lower:
        materials.append('crochet' if 'crochet' in title_lower else 'knit')

    # Build search query
    search_terms = []
    if product_type:
        search_terms.append(product_type)
    search_terms.extend(materials)
    if 'handmade' in title_lower or 'hand' in title_lower:
        search_terms.append('handmade')

    etsy_query = f"etsy {' '.join(search_terms)} price"

    return {
        'etsy_search_query': etsy_query,
        'product_type': product_type,
        'materials': materials,
        'instructions': 'Use WebSearch MCP to search this query and extract pricing data'
    }


def search_market(title, use_websearch=True):
    """Search for similar products - ready for WebSearch MCP integration

    NOTE: This function returns search queries that should be executed
    by Claude using the WebSearch tool. When called from Claude context,
    Claude should:
    1. Use the search queries provided
    2. Execute WebSearch tool calls
    3. Extract pricing and trend data
    4. Return structured market data
    """

    # Generate search queries
    queries = search_market_with_websearch(title)

    # Return instructions for WebSearch integration
    return {
        'search_queries': {
            'etsy_pricing': queries['etsy_search_query'],
            'trends': f"{queries['product_type']} fashion trends 2026" if queries['product_type'] else None,
            'competitors': f"handmade {queries['product_type']} etsy sellers" if queries['product_type'] else None
        },
        'product_type': queries.get('product_type'),
        'materials': queries.get('materials'),
        'websearch_ready': True,
        'note': 'Execute these queries with WebSearch MCP to get real market data'
    }


def generate_report(listing, inventory, images, market_data, listing_id):
    """Generate verification report"""
    report = []
    report.append("🔍 LISTING VERIFICATION REPORT")
    report.append("=" * 60)
    report.append(f"Product: {listing.get('title', 'Unknown')[:50]}...")
    report.append(f"Listing ID: {listing_id}")
    report.append(f"Status: {listing.get('state', 'Unknown').title()}")
    report.append(f"URL: https://www.etsy.com/listing/{listing_id}")
    report.append("")

    # Completeness check
    checks, issues = verify_completeness(listing, inventory, images)
    report.append("✅ COMPLETENESS CHECK")
    report.append("=" * 60)
    for check in checks:
        report.append(check)
    for issue in issues:
        report.append(issue)
    report.append("")

    # Size measurement validation is apparel-specific and should be profile-driven.
    description = listing.get('description', '')
    title = listing.get('title', '')
    size_checks = []
    size_issues = []
    if should_validate_size_measurements() and should_expect_size_variations(title):
        size_checks, size_issues, size_warnings = verify_size_measurements(description, title)
        report.append("📏 SIZE MEASUREMENT VALIDATION")
        report.append("=" * 60)
        for check in size_checks:
            report.append(check)
        for issue in size_issues:
            report.append(issue)
        for warning in size_warnings:
            report.append(warning)
        report.append("")
        issues.extend(size_issues)
    elif should_validate_size_measurements():
        report.append("📏 SIZE MEASUREMENT VALIDATION")
        report.append("=" * 60)
        report.append("✅ Size chart skipped for one-size/non-apparel title")
        report.append("")

    # Pricing verification
    base_price = listing.get('price', {}).get('amount', 0) / listing.get('price', {}).get('divisor', 1)
    price_checks, price_issues = verify_pricing(inventory, base_price)
    report.append("💰 PRICING VERIFICATION")
    report.append("=" * 60)
    for check in price_checks:
        report.append(check)
    for issue in price_issues:
        report.append(issue)
    report.append("")

    # Market research
    if market_data:
        report.append("📊 MARKET RESEARCH")
        report.append("=" * 60)
        report.append(f"Similar items found: {market_data.get('similar_items', 'N/A')}")

        price_range = market_data.get('price_range', {})
        if price_range:
            report.append("")
            report.append("Price Analysis:")
            report.append(f"  • Low: ${price_range.get('low', 0)}")
            report.append(f"  • Median: ${price_range.get('median', 0)}")
            report.append(f"  • High: ${price_range.get('high', 0)}")

            if inventory and 'products' in inventory:
                medium_price = None
                for p in inventory['products']:
                    if p.get('property_values'):
                        size = p['property_values'][0]['values'][0]
                        if size == 'Medium':
                            medium_price = p['offerings'][0]['price']['amount'] / p['offerings'][0]['price']['divisor']
                            break

                if medium_price:
                    median = price_range.get('median', 0)
                    if medium_price > median:
                        diff = ((medium_price - median) / median) * 100
                        report.append(f"  • Your price (M): ${medium_price:.2f} ✅ ({diff:.0f}% above median)")
                    else:
                        report.append(f"  • Your price (M): ${medium_price:.2f}")

        trends = market_data.get('trends', {})
        if trends:
            report.append("")
            report.append("📈 TRENDS:")
            for keyword, change in trends.items():
                report.append(f"  • \"{keyword.replace('_', ' ')}\": {change}")

        report.append("")

    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("=" * 60)

    if len(issues) == 0:
        report.append("✅ Listing is complete and well-optimized!")
    else:
        report.append("Action items:")
        for issue in issues[:5]:  # Top 5 issues
            report.append(f"  • {issue}")

    report.append("")
    report.append("=" * 60)

    # Calculate score (size issues are weighted more heavily)
    total_checks = len(checks) + len(price_checks) + len(size_checks)
    total_issues = len(issues) + len(price_issues)

    # Critical size issues reduce score more significantly
    critical_size_issues = sum(1 for issue in size_issues if 'CRITICAL' in issue)
    if critical_size_issues > 0:
        score = max(0, (total_checks / (total_checks + total_issues + critical_size_issues * 2)) * 10)
    else:
        score = (total_checks / (total_checks + total_issues)) * 10 if (total_checks + total_issues) > 0 else 0

    report.append(f"Overall Score: {score:.1f}/10")
    report.append("")

    return "\\n".join(report)


def save_report(report, product_name, listing_id):
    """Save report to file"""
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{product_name}_{date}_{listing_id}.txt"
    filepath = REPORTS_DIR / filename

    with open(filepath, 'w') as f:
        f.write(report)

    return filepath


def verify_listing(listing_id, product_name=None, quick=False):
    """Main verification function"""
    print(f"\\n🔍 Verifying listing: {listing_id}")
    print("=" * 60)

    # Get access token
    access_token = get_access_token()

    # Fetch listing data
    print("📥 Fetching listing data...")
    listing = get_listing_details(access_token, listing_id)
    if not listing:
        sys.exit(1)

    inventory = get_listing_inventory(access_token, listing_id)
    images = get_listing_images(access_token, listing_id)

    print("✅ Data fetched")
    print("")

    # Market research (skip if quick mode)
    market_data = None
    if not quick:
        print("📊 Conducting market research...")
        title = listing.get('title', '')
        market_data = search_market(title)
        print("✅ Market research complete")
        print("")

    # Generate report
    report = generate_report(listing, inventory, images, market_data, listing_id)

    # Display report
    print(report)

    # Save report
    if not product_name:
        product_name = listing.get('title', 'unknown').lower().replace(' ', '_')[:30]

    filepath = save_report(report, product_name, listing_id)
    print(f"💾 Report saved: {filepath}")
    print("")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Verify Etsy listings from a shop profile')
    parser.add_argument('--listing-id', '-l', type=int, help='Etsy listing ID')
    parser.add_argument('--product', '-p', help='Product name (finds most recent)')
    parser.add_argument('--quick', '-q', action='store_true', help='Skip market research')

    args = parser.parse_args()

    if not args.listing_id and not args.product:
        parser.error("Either --listing-id or --product is required")

    if args.product:
        # TODO: Find most recent listing ID for product
        print("⚠️  Product lookup not yet implemented. Please use --listing-id")
        sys.exit(1)

    verify_listing(args.listing_id, args.product, args.quick)
