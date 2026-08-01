#!/usr/bin/env python3
"""Etsy listing publisher driven by an etsy_shop_profile.yaml profile."""

import sys
import json
import requests
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

from etsy_profile import (
    api_credentials,
    consume_profile_arg,
    first_matching_rule,
    load_profile,
    optional_int,
    project_path,
)

PROFILE = load_profile(consume_profile_arg(sys.argv))
PROJECT_ROOT = Path(PROFILE["paths"]["project_root"])
LISTING_DIR = project_path("listing_dir", profile=PROFILE)
IMAGE_DIR = project_path("image_dir", profile=PROFILE)
TOKEN_FILE = project_path("token_file", profile=PROFILE)
REDIRECT_URI = PROFILE["etsy_api"].get("redirect_uri", "http://localhost:8080/oauth/redirect")
SCOPES = PROFILE["etsy_api"].get("scopes", "listings_w listings_r shops_r shops_w transactions_r")
PUBLISHING = PROFILE.get("publishing", {})
TAXONOMY = PROFILE.get("taxonomy", {})
SHOP_SECTIONS = PROFILE.get("shop_sections", {})
VARIATIONS = PROFILE.get("variations", {})
API_KEY = None
API_SECRET = None

# Etsy API v3 endpoints
AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
API_BASE = "https://openapi.etsy.com/v3/application"


def require_api_credentials():
    """Load Etsy API credentials only for real API calls."""
    global API_KEY, API_SECRET
    if not API_KEY or not API_SECRET:
        API_KEY, API_SECRET = api_credentials(PROFILE)
    return API_KEY, API_SECRET


def api_headers(access_token, *, json_body=False):
    api_key, api_secret = require_api_credentials()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'x-api-key': f'{api_key}:{api_secret}',
    }
    if json_body:
        headers['Content-Type'] = 'application/json'
    return headers


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth callback from Etsy"""

    auth_code = None

    def do_GET(self):
        """Handle the OAuth callback"""
        query = parse_qs(urlparse(self.path).query)

        if 'code' in query:
            OAuthCallbackHandler.auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress logging"""
        pass


def get_authorization():
    """Start OAuth flow and get authorization code"""
    print("\n🔐 Starting OAuth Authorization Flow...")
    api_key, _api_secret = require_api_credentials()

    # Step 1: Generate authorization URL
    params = {
        'response_type': 'code',
        'client_id': api_key,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': 'hazumi_auth'
    }

    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print(f"\n📖 Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")

    # Start local server to receive callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server_thread = Thread(target=server.handle_request)
    server_thread.start()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback
    print("⏳ Waiting for authorization...")
    server_thread.join(timeout=300)

    if OAuthCallbackHandler.auth_code:
        print("✅ Authorization code received!")
        return OAuthCallbackHandler.auth_code
    else:
        print("❌ Authorization failed or timed out")
        sys.exit(1)


def exchange_code_for_token(auth_code):
    """Exchange authorization code for access token"""
    print("\n🔄 Exchanging code for access token...")
    api_key, api_secret = require_api_credentials()

    data = {
        'grant_type': 'authorization_code',
        'client_id': api_key,
        'redirect_uri': REDIRECT_URI,
        'code': auth_code
    }

    # Base64 encode client_id:client_secret for Basic Auth
    import base64
    auth_string = f"{api_key}:{api_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=45)

    if response.status_code == 200:
        token_data = response.json()
        print("✅ Access token received!")

        # Save token for future use
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

        print(f"💾 Token saved to: {TOKEN_FILE}")
        return token_data
    else:
        print(f"❌ Token exchange failed: {response.status_code}")
        print(response.text)
        sys.exit(1)


def refresh_access_token(refresh_token):
    """Refresh expired access token"""
    print("\n🔄 Refreshing access token...")
    api_key, _api_secret = require_api_credentials()

    data = {
        'grant_type': 'refresh_token',
        'client_id': api_key,
        'refresh_token': refresh_token
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(TOKEN_URL, json=data, headers=headers, timeout=45)

    if response.status_code == 200:
        token_data = response.json()
        print("✅ Token refreshed!")

        token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)

        # Save new token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

        return token_data
    else:
        print(f"❌ Token refresh failed: {response.status_code}")
        return None


def get_access_token():
    """Get valid access token (from file or new OAuth flow)"""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        # Check if token is expired
        if 'expires_at' in token_data:
            if time.time() < token_data['expires_at']:
                return token_data['access_token']

        # Try to refresh
        if 'refresh_token' in token_data:
            new_token_data = refresh_access_token(token_data['refresh_token'])
            if new_token_data:
                return new_token_data['access_token']

    # Need new authorization. Etsy OAuth now expects PKCE for this app flow.
    print("\n⚠️  No valid token found. Starting PKCE OAuth flow...")
    from oauth_pkce import start_oauth_flow, exchange_code_for_token
    auth_code, code_verifier = start_oauth_flow()
    token_data = exchange_code_for_token(auth_code, code_verifier)

    return token_data['access_token']


def get_shop_id(access_token):
    """Get the shop ID for the authenticated user"""
    # The access token contains the user ID as a prefix
    user_id = access_token.split('.')[0]

    headers = api_headers(access_token)

    # Get user's shops
    response = requests.get(f"{API_BASE}/users/{user_id}/shops", headers=headers, timeout=45)

    if response.status_code == 200:
        shop_data = response.json()

        # Response might be a single shop object or have results array
        if isinstance(shop_data, dict) and 'shop_id' in shop_data:
            # Single shop response
            shop_id = shop_data['shop_id']
            shop_name = shop_data.get('shop_name', 'Unknown')
            print(f"✅ Found shop: {shop_name} (ID: {shop_id})")
            return shop_id
        elif 'results' in shop_data:
            # Array response
            shops = shop_data['results']
            if shops:
                shop_id = shops[0]['shop_id']
                shop_name = shops[0].get('shop_name', 'Unknown')
                print(f"✅ Found shop: {shop_name} (ID: {shop_id})")
                return shop_id

    print(f"❌ Could not get shop ID: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    sys.exit(1)


def parse_listing_file(file_path):
    """Parse listing .txt file"""
    import re

    content = file_path.read_text(encoding='utf-8')

    def extract_hash_section(section_name, next_sections):
        pattern = (
            rf'##\s*{re.escape(section_name)}\s*\n'
            rf'(.*?)'
            rf'(?=\n##\s*(?:{"|".join(map(re.escape, next_sections))})\b|\Z)'
        )
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Newer listing files use Markdown headings so they can be parsed by humans
    # and scripts without depending on punctuation in the heading line.
    if '## TITLE' in content:
        title = extract_hash_section('TITLE', ['DESCRIPTION'])
        description = extract_hash_section('DESCRIPTION', ['TAGS', 'MATERIAL TAGS', 'ATTRIBUTES'])
        tags_text = extract_hash_section('TAGS', ['MATERIAL TAGS', 'ATTRIBUTES'])
        materials_text = extract_hash_section('MATERIAL TAGS', ['ATTRIBUTES'])

        tags = [
            tag.strip().lstrip('•*-').strip()
            for tag in tags_text.split('\n')
            if tag.strip() and not tag.strip().startswith('=')
        ][:13]
        materials = [
            material.strip().lstrip('•*-').strip()
            for material in materials_text.split('\n')
            if material.strip()
        ]

        return {
            'title': title,
            'description': description,
            'tags': tags,
            'materials': materials,
        }

    # Extract title (after "TITLE" line)
    title_match = re.search(r'TITLE.*?:\s*\n(.+?)(?:\n\n|$)', content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # Extract description (after "DESCRIPTION:" until next section)
    desc_match = re.search(r'DESCRIPTION:\s*\n(.*?)(?=\n(?:TAGS|MATERIALS|OCCASION|STYLE|TAXONOMY))', content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # Extract tags (lines between "TAGS" and next section)
    tags_match = re.search(r'TAGS.*?:\s*\n(.*?)(?=\n(?:MATERIALS|OCCASION|STYLE|TAXONOMY))', content, re.DOTALL)
    if tags_match:
        tags_text = tags_match.group(1)
        # Split by newlines and clean each tag
        tags = [tag.strip() for tag in tags_text.split('\n') if tag.strip() and not tag.startswith('=')][:13]
    else:
        tags = []

    # Extract materials (lines between "MATERIALS:" and next section)
    materials = []
    materials_match = re.search(r'MATERIALS:\s*\n(.*?)(?=\n(?:OCCASION|STYLE|TAXONOMY))', content, re.DOTALL)
    if materials_match:
        for line in materials_match.group(1).split('\n'):
            line = line.strip()
            if line and line.startswith('•'):
                material = line.lstrip('•').strip()
                if material:
                    materials.append(material)

    return {
        'title': title,
        'description': description,
        'tags': tags,
        'materials': materials,
    }


def determine_taxonomy_id(title):
    """Determine category from title"""
    return (
        first_matching_rule(title, TAXONOMY.get("rules", []), "taxonomy_id", "taxonomy_id_env")
        or optional_int(TAXONOMY, "default_taxonomy_id", "default_taxonomy_id_env")
        or 550
    )


def get_shop_section_id(title):
    """Determine shop section from title"""
    return first_matching_rule(title, SHOP_SECTIONS.get("rules", []), "section_id", "section_id_env")


def build_listing_payload(listing_data, price):
    """Build Etsy create-listing payload from the project profile."""
    payload = {
        'quantity': int(PUBLISHING.get("quantity", 50)),
        'title': listing_data['title'],
        'description': listing_data['description'],
        'price': price,
        'who_made': PUBLISHING.get("who_made", "i_did"),
        'when_made': PUBLISHING.get("when_made", "made_to_order"),
        'is_made_from_scratch': bool(PUBLISHING.get("is_made_from_scratch", True)),
        'taxonomy_id': determine_taxonomy_id(listing_data['title']),
        'tags': [tag.strip() for tag in listing_data['tags'][:13]],
        'materials': listing_data['materials'],
        'is_supply': bool(PUBLISHING.get("is_supply", False)),
        'production_partner_ids': [],
        'type': PUBLISHING.get("type", "physical"),
        'item_weight_unit': 'oz',
        'should_auto_renew': bool(PUBLISHING.get("should_auto_renew", True)),
        'processing_min': int(PUBLISHING.get("processing_min", 5)),
        'processing_max': int(PUBLISHING.get("processing_max", 10)),
        'shop_section_id': get_shop_section_id(listing_data['title']),
        'state': PUBLISHING.get("default_state", "draft"),
        'language': PUBLISHING.get("language", "en-US"),
    }

    shipping_profile_id = optional_int(PUBLISHING, "shipping_profile_id", "shipping_profile_id_env")
    readiness_state_id = optional_int(PUBLISHING, "readiness_state_id", "readiness_state_id_env")
    if shipping_profile_id:
        payload['shipping_profile_id'] = shipping_profile_id
    if readiness_state_id:
        payload['readiness_state_id'] = readiness_state_id

    return payload


def create_draft_listing(access_token, shop_id, listing_data, price):
    """Create draft listing on Etsy"""
    print("\n📝 Creating draft listing...")

    headers = api_headers(access_token, json_body=True)
    payload = build_listing_payload(listing_data, price)

    endpoint = f"{API_BASE}/shops/{shop_id}/listings"
    if "readiness_state_id" in payload:
        endpoint = f"{endpoint}?legacy=false"

    response = requests.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=45
    )

    if response.status_code == 201:
        listing = response.json()
        listing_id = listing['listing_id']
        print(f"✅ Draft listing created! ID: {listing_id}")
        return listing_id
    else:
        print(f"❌ Failed to create listing: {response.status_code}")
        print(response.text)
        return None


def upload_images(access_token, shop_id, listing_id, image_files):
    """Upload images to listing"""
    print(f"\n📸 Uploading {len(image_files)} images...")

    headers = api_headers(access_token)

    uploaded_count = 0
    for idx, image_path in enumerate(image_files[:10], 1):
        print(f"   Uploading {image_path.name}...")

        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'rank': idx}

            response = requests.post(
                f"{API_BASE}/shops/{shop_id}/listings/{listing_id}/images",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )

            if response.status_code == 201:
                uploaded_count += 1
                print(f"   ✅ Uploaded ({idx}/{len(image_files[:10])})")
            else:
                print(f"   ⚠️  Upload failed: {response.status_code}")

    print(f"✅ Uploaded {uploaded_count} images")
    return uploaded_count


def find_product_images(product_name):
    """Find images in product-specific folder"""
    # Look for product-specific folder
    product_folder = IMAGE_DIR / product_name.replace(' ', '_')

    if product_folder.exists() and product_folder.is_dir():
        # Get all PNG files in product folder
        matches = list(product_folder.glob('*.png'))
        matches.sort(key=lambda f: f.name)
        return matches[:10]

    # Fallback: search for matching images across all folders
    keywords = product_name.lower().split()
    all_folders = [f for f in IMAGE_DIR.iterdir() if f.is_dir()]

    matches = []
    for folder in all_folders:
        folder_name_lower = folder.name.lower()
        if all(keyword in folder_name_lower for keyword in keywords):
            matches.extend(list(folder.glob('*.png')))

    if matches:
        matches.sort(key=lambda f: f.name)
        return matches[:10]

    return []


def find_listing_file(product_name):
    """Find listing file by product name"""
    keywords = product_name.lower().split()
    txt_files = list(LISTING_DIR.glob('*.txt'))

    matches = []
    for file in txt_files:
        file_name_lower = file.stem.lower()
        if all(keyword in file_name_lower for keyword in keywords):
            matches.append(file)

    if not matches:
        return None

    # Prefer _FINAL files
    final_files = [f for f in matches if '_FINAL' in f.stem or '_final' in f.stem]
    if final_files:
        return max(final_files, key=lambda f: f.stat().st_mtime)

    return max(matches, key=lambda f: f.stat().st_mtime)


def create_size_variations(access_token, shop_id, listing_id, base_price):
    """Create size variations (S, M, L) with inventory"""
    if not VARIATIONS.get("enabled", True):
        print("\n📦 Size variations skipped by project profile")
        return True

    print("\n📦 Creating size variations...")

    headers = api_headers(access_token, json_body=True)
    size_property_id = int(VARIATIONS.get("size_property_id"))
    readiness_state_id = optional_int(PUBLISHING, "readiness_state_id", "readiness_state_id_env")
    products = []
    for size in VARIATIONS.get("sizes", []):
        offering = {
            "price": base_price + float(size.get("price_delta", 0)),
            "quantity": int(size.get("quantity", PUBLISHING.get("quantity", 50))),
            "is_enabled": True,
        }
        if readiness_state_id:
            offering["readiness_state_id"] = readiness_state_id
        products.append({
            "property_values": [
                {
                    "property_id": size_property_id,
                    "property_name": "Size",
                    "scale_id": None,
                    "value_ids": [int(size["value_id"])],
                    "values": [size["name"]],
                }
            ],
            "offerings": [offering],
        })

    # Create inventory with size variations
    inventory_payload = {
        "products": products,
        "price_on_property": [size_property_id] if VARIATIONS.get("price_on_property", True) else [],
        "quantity_on_property": [],
        "sku_on_property": []
    }

    response = requests.put(
        f"{API_BASE}/listings/{listing_id}/inventory",
        headers=headers,
        json=inventory_payload,
        timeout=45
    )

    if response.status_code == 200:
        summary = ", ".join(
            f"{size['name']}=${base_price + float(size.get('price_delta', 0)):.2f}"
            for size in VARIATIONS.get("sizes", [])
        )
        print(f"✅ Size variations created: {summary}")
        return True
    else:
        print(f"⚠️  Failed to create size variations: {response.status_code}")
        print(response.text[:200])
    return False


def should_create_size_variations(title):
    """Only apparel listings should receive clothing size variations."""
    if not VARIATIONS.get("enabled", True):
        return False
    title_lower = title.lower()
    non_apparel_terms = VARIATIONS.get("skip_if_title_contains", [])
    if any(term in title_lower for term in non_apparel_terms):
        return False
    return True


def set_listing_attributes(access_token, shop_id, listing_id, title):
    """Set product attributes based on product type"""
    print("\n🏷️  Setting product attributes...")

    configured_attributes = PROFILE.get("attributes", {}).get("listing_attributes", [])
    if not configured_attributes:
        print("ℹ️  No listing attributes configured in shop profile; skipping attributes")
        return True

    headers = api_headers(access_token, json_body=True)

    attributes = configured_attributes

    # Send PATCH request to update attributes
    response = requests.patch(
        f"{API_BASE}/shops/{shop_id}/listings/{listing_id}",
        headers=headers,
        json={"attributes": attributes},
        timeout=45
    )

    if response.status_code == 200:
        print(f"✅ Attributes set ({len(attributes)} attributes)")
        return True
    else:
        print(f"⚠️  Failed to set attributes: {response.status_code}")
        print(response.text[:200])
        return False


def variation_summary(base_price):
    if not VARIATIONS.get("enabled", True):
        return "none"
    return ", ".join(
        f"{size['name']}=${base_price + float(size.get('price_delta', 0)):.2f}"
        for size in VARIATIONS.get("sizes", [])
    )


def publish_listing(product_name, price, dry_run=False):
    """Main function to publish a listing"""
    print(f"\n🚀 Publishing: {product_name} at ${price}")
    print("="*60)

    # Find listing file
    listing_file = find_listing_file(product_name)
    if not listing_file:
        print(f"❌ Could not find listing file for '{product_name}'")
        print("\nAvailable listings:")
        for f in LISTING_DIR.glob('*.txt'):
            print(f"   - {f.stem}")
        sys.exit(1)

    print(f"✅ Found listing: {listing_file.name}")

    # Parse listing data
    listing_data = parse_listing_file(listing_file)
    print(f"✅ Parsed: {listing_data['title'][:50]}...")

    images = find_product_images(product_name)

    if dry_run:
        payload = build_listing_payload(listing_data, price)
        print("\n🧪 Dry run enabled - no Etsy API calls will be made.")
        print(f"✅ Listing file: {listing_file}")
        print(f"✅ Images found: {len(images)}")
        for image in images:
            print(f"   - {image.name}")
        print(f"✅ Title length: {len(payload['title'])}")
        print(f"✅ Tags: {len(payload['tags'])}")
        print(f"✅ Materials: {len(payload['materials'])}")
        print(f"✅ Taxonomy ID: {payload['taxonomy_id']}")
        print(f"✅ State: {payload['state']}")
        print(f"✅ Variations: {variation_summary(price) if should_create_size_variations(listing_data['title']) else 'none'}")
        missing_optional = []
        if 'shipping_profile_id' not in payload:
            missing_optional.append("shipping profile")
        if 'readiness_state_id' not in payload:
            missing_optional.append("readiness state")
        if missing_optional:
            print(f"⚠️  Optional Etsy settings not configured: {', '.join(missing_optional)}")
        return {
            "listing_file": str(listing_file),
            "image_count": len(images),
            "payload": payload,
        }

    # Get access token
    access_token = get_access_token()

    # Get shop ID
    shop_id = get_shop_id(access_token)

    # Create draft listing
    listing_id = create_draft_listing(access_token, shop_id, listing_data, price)
    if not listing_id:
        sys.exit(1)

    # Upload images
    if images:
        print(f"✅ Found {len(images)} images")
        upload_images(access_token, shop_id, listing_id, images)
    else:
        print("⚠️  No images found")

    # Create size variations only for apparel
    if should_create_size_variations(listing_data['title']):
        create_size_variations(access_token, shop_id, listing_id, price)
    else:
        print("\n📦 Skipping size variations for non-apparel listing")

    # Set attributes
    set_listing_attributes(access_token, shop_id, listing_id, listing_data['title'])

    # Print success
    print("\n" + "="*60)
    print("✅ Listing published to Etsy!")
    print(f"🔗 https://www.etsy.com/listing/{listing_id}")
    if should_create_size_variations(listing_data['title']):
        print(f"📦 Sizes: {variation_summary(price)}")
    else:
        print("📦 Variations: none")
    print(f"📸 Images: {len(images)} uploaded")
    print(f"📋 Status: Draft (activate on Etsy.com)")
    print("="*60 + "\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Publish Etsy listings from a shop profile')
    parser.add_argument('--listing', '-l', help='Product name or keywords')
    parser.add_argument('--price', '-p', type=float, help='Price in dollars')
    parser.add_argument('--auth', action='store_true', help='Authorize with Etsy (run this first)')
    parser.add_argument('--dry-run', action='store_true', help='Build payload without Etsy API calls')

    args = parser.parse_args()

    if args.auth:
        # Force new authorization
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        get_access_token()
        print("\n✅ Authorization complete!")
        sys.exit(0)

    # For publishing, listing and price are required
    if not args.listing or not args.price:
        parser.error("--listing and --price are required (unless using --auth)")

    publish_listing(args.listing, args.price, dry_run=args.dry_run)
