name: etsy-customer-service
version: 1.0.0
title: Etsy Customer Service Assistant
description: |
  End-to-end Etsy customer service workflow powered by opencli:
  - Read unread messages from Etsy Messages inbox
  - Extract conversation context, order details, and product info
  - Generate professional reply drafts based on shop branding
  - Send replies with user confirmation
  - Support multi-shop configuration via opencli profiles

triggers:
  - "reply to etsy messages"
  - "check etsy customer service"
  - "respond to etsy buyers"
  - "handle etsy conversations"

environment:
  required_tools:
    - opencli

config_file: shop_config.yaml
