# Etsy Shop Profile Schema

Use a YAML profile to keep shop-specific values out of reusable skills and scripts.

```yaml
profile_version: 1
shop:
  name: HazumiCrafts
  shop_id: 20691319

paths:
  project_root: /Users/I742076/.claude/projects/hazumi
  listing_dir: listing_seo
  image_dir: image_processing/output
  token_file: etsy_publisher/.etsy_token.json
  reports_dir: listing_verifier/reports

etsy_api:
  api_key_env: ETSY_API_KEY
  api_secret_env: ETSY_API_SECRET
  redirect_uri: http://localhost:8080/oauth/redirect
  scopes: listings_w listings_r shops_r shops_w transactions_r

publishing:
  default_state: draft
  language: en-US
  quantity: 50
  processing_min: 5
  processing_max: 10
  shipping_profile_id: 189946403624
  readiness_state_id: 1408507540467
  who_made: i_did
  when_made: made_to_order
  is_made_from_scratch: true
  is_supply: false
  type: physical
  should_auto_renew: true

taxonomy:
  default_taxonomy_id: 550
  rules:
    - match_any: ["cardigan"]
      taxonomy_id: 549

shop_sections:
  rules:
    - match_any: ["cardigan"]
      section_id: 56146765

variations:
  enabled: true
  skip_if_title_contains: ["hacky", "footbag"]
  size_property_id: 52047899294
  price_on_property: true
  sizes:
    - name: Small
      value_id: 6197759476
      price_delta: -5
      quantity: 50
    - name: Medium
      value_id: 6197759477
      price_delta: 0
      quantity: 50
    - name: Large
      value_id: 6197759478
      price_delta: 5
      quantity: 50

verification:
  min_images: 4
  expected_size_names: ["Small", "Medium", "Large"]
  expected_quantity_per_variation: 50
  expected_price_increment: 5

auto_fix:
  allow_description_size_chart_fix: true
  dry_run_default: true
```

Use env var names for API credentials. Token files may be shop-specific and can remain under the project directory. A second shop should get a second profile with the same schema and different IDs/paths/rules.
