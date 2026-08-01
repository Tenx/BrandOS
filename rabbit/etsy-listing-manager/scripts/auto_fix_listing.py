#!/usr/bin/env python3
"""
Auto-fix Etsy Listing Issues
Automatically corrects size measurements and other issues detected during verification
"""

import sys
import requests
import re
from pathlib import Path

# Import verification functions
sys.path.append(str(Path(__file__).parent))
from verify_listing import (
    API_BASE,
    api_headers,
    PROFILE,
    get_access_token,
    get_listing_details,
    get_listing_inventory,
    get_listing_images,
    verify_completeness,
    verify_pricing,
    verify_size_measurements
)

AUTO_FIX = PROFILE.get("auto_fix", {})


def fix_size_measurements(description, title, issues):
    """
    Automatically fix size measurement issues in description
    Returns: (fixed_description, changes_made)
    """
    changes = []
    fixed_desc = description

    # Parse current measurements
    size_chart_pattern = r'Size Chart:.*?(?=\n\n|$)'
    size_chart_match = re.search(size_chart_pattern, description, re.DOTALL | re.IGNORECASE)

    if not size_chart_match:
        changes.append("❌ Cannot auto-fix: No size chart found")
        return fixed_desc, changes

    size_chart = size_chart_match.group(0)

    # Extract measurements for each size
    measurements = {}
    for size in ['S', 'M', 'L']:
        pattern = rf'•\s*{size}:\s*Bust\s*([\d-]+)cm.*?Length\s*([\d]+)cm.*?(?:Sleeve\s*([\d]+)cm)?'
        match = re.search(pattern, size_chart)

        if match:
            bust_range = match.group(1)
            length = int(match.group(2))
            sleeve = int(match.group(3)) if match.group(3) else None

            if '-' in bust_range:
                bust_min, bust_max = map(int, bust_range.split('-'))
            else:
                bust_min = bust_max = int(bust_range)

            measurements[size] = {
                'bust_min': bust_min,
                'bust_max': bust_max,
                'length': length,
                'sleeve': sleeve
            }

    # Check for issues and fix them
    if len(measurements) == 3:
        # Determine garment type and get realistic measurements
        title_lower = title.lower()
        is_oversized = 'oversized' in title_lower or 'chunky' in title_lower
        is_dress = 'dress' in title_lower or 'maxi' in title_lower
        is_top = 'top' in title_lower or 'crop' in title_lower

        # Fix bust progression if needed
        s_bust_avg = (measurements['S']['bust_min'] + measurements['S']['bust_max']) / 2
        m_bust_avg = (measurements['M']['bust_min'] + measurements['M']['bust_max']) / 2
        l_bust_avg = (measurements['L']['bust_min'] + measurements['L']['bust_max']) / 2

        needs_fix = False

        # Check if progression is wrong
        if not (s_bust_avg < m_bust_avg < l_bust_avg):
            needs_fix = True
            changes.append("⚠️ Bust progression was incorrect")

        # Check if increments are unrealistic
        s_to_m = m_bust_avg - s_bust_avg
        m_to_l = l_bust_avg - m_bust_avg

        if s_to_m < 3 or s_to_m > 10 or m_to_l < 3 or m_to_l > 10:
            needs_fix = True
            changes.append("⚠️ Bust increments were unrealistic")

        # Check if absolute values are unrealistic
        if is_oversized and (m_bust_avg < 95 or m_bust_avg > 135):
            needs_fix = True
            changes.append("⚠️ Bust measurement unrealistic for oversized")
        elif not is_oversized and (m_bust_avg < 80 or m_bust_avg > 125):
            needs_fix = True
            changes.append("⚠️ Bust measurement unrealistic")

        if needs_fix:
            # Generate realistic measurements
            if is_oversized:
                # Oversized: larger bust measurements
                new_measurements = {
                    'S': {'bust': (100, 106), 'length': 60, 'sleeve': 58},
                    'M': {'bust': (107, 114), 'length': 62, 'sleeve': 59},
                    'L': {'bust': (115, 122), 'length': 64, 'sleeve': 60}
                }
            elif is_dress:
                # Maxi dress
                new_measurements = {
                    'S': {'bust': (80, 85), 'length': 140, 'sleeve': None},
                    'M': {'bust': (86, 92), 'length': 143, 'sleeve': None},
                    'L': {'bust': (93, 98), 'length': 146, 'sleeve': None}
                }
            elif is_top:
                # Regular top
                new_measurements = {
                    'S': {'bust': (80, 86), 'length': 55, 'sleeve': 58},
                    'M': {'bust': (87, 93), 'length': 57, 'sleeve': 59},
                    'L': {'bust': (94, 100), 'length': 59, 'sleeve': 60}
                }
            else:
                # Regular sweater/cardigan
                new_measurements = {
                    'S': {'bust': (85, 90), 'length': 60, 'sleeve': 58},
                    'M': {'bust': (91, 97), 'length': 62, 'sleeve': 59},
                    'L': {'bust': (98, 104), 'length': 64, 'sleeve': 60}
                }

            # Replace size chart in description
            new_size_chart_lines = []
            for size in ['S', 'M', 'L']:
                bust_min, bust_max = new_measurements[size]['bust']
                bust_min_in = int(bust_min / 2.54)
                bust_max_in = int(bust_max / 2.54)
                length_cm = new_measurements[size]['length']
                length_in = int(length_cm / 2.54)

                if new_measurements[size]['sleeve']:
                    sleeve_cm = new_measurements[size]['sleeve']
                    sleeve_in = int(sleeve_cm / 2.54)
                    line = f"• {size}: Bust {bust_min}-{bust_max}cm/{bust_min_in}-{bust_max_in}\", Length {length_cm}cm/{length_in}\", Sleeve {sleeve_cm}cm/{sleeve_in}\""
                else:
                    line = f"• {size}: Bust {bust_min}-{bust_max}cm/{bust_min_in}-{bust_max_in}\", Length {length_cm}cm/{length_in}\""

                new_size_chart_lines.append(line)

            # Find and replace the size chart section
            new_size_chart = "Size Chart:\n" + "\n".join(new_size_chart_lines)
            fixed_desc = re.sub(
                r'Size Chart:.*?(?=\n\n)',
                new_size_chart,
                description,
                flags=re.DOTALL
            )

            changes.append("✅ Auto-fixed size measurements to realistic values")
            changes.append(f"   S: Bust {new_measurements['S']['bust'][0]}-{new_measurements['S']['bust'][1]}cm, Length {new_measurements['S']['length']}cm")
            changes.append(f"   M: Bust {new_measurements['M']['bust'][0]}-{new_measurements['M']['bust'][1]}cm, Length {new_measurements['M']['length']}cm")
            changes.append(f"   L: Bust {new_measurements['L']['bust'][0]}-{new_measurements['L']['bust'][1]}cm, Length {new_measurements['L']['length']}cm")

    return fixed_desc, changes


def update_listing_description(access_token, shop_id, listing_id, new_description):
    """Update listing description via Etsy API"""
    headers = api_headers(access_token)
    headers['Content-Type'] = 'application/json'

    payload = {
        'description': new_description
    }

    response = requests.patch(
        f'{API_BASE}/shops/{shop_id}/listings/{listing_id}',
        headers=headers,
        json=payload
    )

    return response.status_code == 200


def auto_fix_listing(listing_id, dry_run=False):
    """
    Main auto-fix function
    dry_run=True: Only report what would be fixed, don't apply changes
    dry_run=False: Apply fixes automatically
    """
    print(f"\n🔧 Auto-Fix Analysis: Listing {listing_id}")
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

    title = listing.get('title', '')
    description = listing.get('description', '')
    shop_id = listing.get('shop_id')

    print("✅ Data fetched")
    print("")

    # Run verification to detect issues
    print("🔍 Detecting issues...")
    checks, issues = verify_completeness(listing, inventory, images)
    size_issues = []
    if AUTO_FIX.get("allow_description_size_chart_fix", False):
        size_checks, size_issues, size_warnings = verify_size_measurements(description, title)

    all_issues = issues + size_issues

    if not all_issues:
        print("✅ No issues detected! Listing is perfect.")
        return

    print(f"⚠️  Found {len(all_issues)} issue(s):")
    for issue in all_issues:
        print(f"   {issue}")
    print("")

    # Attempt to fix size measurement issues
    if size_issues:
        print("🔧 Attempting to fix size measurements...")
        fixed_description, changes = fix_size_measurements(description, title, size_issues)

        if changes and fixed_description != description:
            print("\n📝 Proposed changes:")
            for change in changes:
                print(f"   {change}")

            if dry_run:
                print("\n⚠️  DRY RUN MODE - No changes applied")
                print("   Run without --dry-run to apply fixes")
            else:
                print("\n📤 Applying fixes to Etsy listing...")
                success = update_listing_description(access_token, shop_id, listing_id, fixed_description)

                if success:
                    print("✅ Listing updated successfully!")
                    print(f"🔗 View: https://www.etsy.com/listing/{listing_id}")
                else:
                    print("❌ Failed to update listing")
        else:
            print("⚠️  Could not auto-fix size measurements")
            print("   Manual review required")
    else:
        print("✅ Size measurements are correct")

    print("")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-fix Etsy listing issues")
    parser.add_argument('--listing-id', type=str, required=True, help='Etsy listing ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without applying')

    args = parser.parse_args()

    auto_fix_listing(args.listing_id, dry_run=args.dry_run)
