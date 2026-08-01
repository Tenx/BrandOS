#!/usr/bin/env python3
"""Batch update Etsy listing prices from a target JSON file."""

import argparse
import json
import sys
from pathlib import Path

import requests

from etsy_profile import api_credentials, consume_profile_arg, load_profile, project_path


PROFILE = load_profile(consume_profile_arg(sys.argv))
SHOP = PROFILE.get("shop", {})
TOKEN_FILE = project_path("token_file", profile=PROFILE)
API_BASE = "https://openapi.etsy.com/v3/application"
API_KEY = None
API_SECRET = None


def require_api_credentials():
    global API_KEY, API_SECRET
    if not API_KEY or not API_SECRET:
        API_KEY, API_SECRET = api_credentials(PROFILE)
    return API_KEY, API_SECRET


def api_headers(access_token, *, json_body=False):
    api_key, api_secret = require_api_credentials()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": f"{api_key}:{api_secret}",
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def access_token():
    if not TOKEN_FILE.exists():
        raise RuntimeError(
            "No Etsy token file found. Run publish_to_etsy.py --auth after setting API credentials."
        )
    token_data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    token = token_data.get("access_token")
    if not token:
        raise RuntimeError("Token file does not contain access_token.")
    return token


def money_value(offering):
    price = offering.get("price", {})
    amount = price.get("amount")
    divisor = price.get("divisor", 100)
    if amount is None:
        return None
    return float(amount) / float(divisor)


def product_label(product):
    values = []
    for property_value in product.get("property_values", []):
        values.extend(property_value.get("values", []))
    return values[0] if values else "single"


def set_offering_price(offering, price):
    offering["price"] = float(price)


def fetch_inventory(token, listing_id):
    response = requests.get(
        f"{API_BASE}/listings/{listing_id}/inventory",
        headers=api_headers(token),
        timeout=45,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch inventory for {listing_id}: {response.status_code} {response.text[:300]}"
        )
    return response.json()


def update_inventory(token, listing_id, inventory):
    payload = {
        "products": [sanitize_product(product) for product in inventory.get("products", [])],
        "price_on_property": inventory.get("price_on_property", []),
        "quantity_on_property": inventory.get("quantity_on_property", []),
        "sku_on_property": inventory.get("sku_on_property", []),
    }
    response = requests.put(
        f"{API_BASE}/listings/{listing_id}/inventory",
        headers=api_headers(token, json_body=True),
        json=payload,
        timeout=45,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to update inventory for {listing_id}: {response.status_code} {response.text[:300]}"
        )
    return response.json()


def sanitize_property_value(property_value):
    return {
        "property_id": property_value.get("property_id"),
        "property_name": property_value.get("property_name"),
        "scale_id": property_value.get("scale_id"),
        "value_ids": property_value.get("value_ids", []),
        "values": property_value.get("values", []),
    }


def sanitize_offering(offering):
    clean = {
        "price": offering.get("price"),
        "quantity": int(offering.get("quantity", 0)),
        "is_enabled": bool(offering.get("is_enabled", True)),
    }
    if offering.get("readiness_state_id") is not None:
        clean["readiness_state_id"] = offering.get("readiness_state_id")
    return clean


def sanitize_product(product):
    return {
        "sku": product.get("sku", ""),
        "property_values": [
            sanitize_property_value(value)
            for value in product.get("property_values", [])
        ],
        "offerings": [
            sanitize_offering(offering)
            for offering in product.get("offerings", [])
        ],
    }


def target_price_for_product(product, target):
    variations = target.get("variations") or {}
    if variations:
        label = product_label(product)
        if label not in variations:
            raise RuntimeError(
                f"Listing {target['listing_id']} has variation {label!r}, but no target price for it."
            )
        return float(variations[label])
    if "single_price" in target:
        return float(target["single_price"])
    return float(target["base_price"])


def plan_changes(inventory, target):
    changes = []
    for product in inventory.get("products", []):
        label = product_label(product)
        next_price = target_price_for_product(product, target)
        for offering in product.get("offerings", []):
            current_price = money_value(offering)
            changes.append((label, current_price, next_price))
            set_offering_price(offering, next_price)
    return changes


def run(targets_path, dry_run):
    targets_doc = json.loads(Path(targets_path).read_text(encoding="utf-8"))
    token = access_token()
    results = []
    for target in targets_doc.get("targets", []):
        listing_id = int(target["listing_id"])
        name = target.get("product_name", "")
        inventory = fetch_inventory(token, listing_id)
        changes = plan_changes(inventory, target)
        print(f"\n{listing_id} {name}")
        for label, current, next_price in changes:
            print(f"  {label}: {current:.2f} -> {next_price:.2f}")
        if not dry_run:
            update_inventory(token, listing_id, inventory)
            print("  updated")
        else:
            print("  dry-run only")
        results.append({"listing_id": listing_id, "name": name, "changes": changes})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", required=True, help="Path to price_update_targets JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without updating Etsy")
    args = parser.parse_args()
    run(args.targets, args.dry_run)


if __name__ == "__main__":
    main()
