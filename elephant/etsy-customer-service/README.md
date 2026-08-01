# Etsy Customer Service Skill

End-to-end Etsy customer service workflow powered by **opencli** and **Etsy API v3**:
- ✅ Read unread messages from Etsy Messages inbox
- ✅ Extract conversation context, order details, and product info
- ✅ **Verify order status via Etsy API** (shipped/not shipped, tracking)
- ✅ **Issue refunds and cancel orders automatically** via Etsy API
- ✅ Generate professional reply drafts based on shop branding
- ✅ Send replies with user confirmation
- ✅ Support multi-shop configuration
- ✅ **Support multiple Chrome profiles** (one per shop)

## Installation

1. **Install opencli** (if not already installed):
   ```bash
   npm install -g opencli
   ```

2. **Set up Etsy API access**:
   ```bash
   # Run OAuth flow (opens browser for authorization)
   python3 etsy_publisher/oauth_pkce.py

   # This creates .etsy_token.json with API credentials
   ```

3. **Link this skill**:
   ```bash
   ln -s ~/.codex/skills/etsy-customer-service ~/.claude/skills/etsy-customer-service
   ```

4. **Configure your shop** in `shop_config.yaml`:
   - Set your shop name, brand voice, and policies
   - Customize reply templates for different message types

## Usage

### On-Demand (Recommended)

Use the skill whenever you need to handle customer messages:

```
Check my Etsy messages
Reply to unread messages
```

No background monitoring needed - trigger when you're ready to respond.

### Check Unread Messages
```
Check my Etsy messages
```

### Reply to All Unread
```
Reply to my unread Etsy messages
```

### Draft Reply for Specific Buyer
```
Draft a reply to [buyer name] about [topic]
```

## Configuration

Edit `shop_config.yaml` to customize:

- **Brand voice**: tone, emoji usage, signature
- **Reply templates**: sizing inquiry, refund request, shipping concern, etc.
- **Shop policies**: production time, refund window, shipping times
- **Auto-greetings**: messages for first-time buyers

## Message Types

The skill automatically categorizes messages:

1. **Sizing Inquiry**: Buyer asks about fit, measurements, size recommendations
2. **Refund Request**: Buyer wants to cancel or return order
3. **Shipping Concern**: Buyer worried about delivery time or tracking
4. **Order Modification**: Buyer wants to change product details
5. **General Inquiry**: Product questions, customization requests

Each type uses a tailored response template from your config.

## Features

### Context-Aware Replies
- Reads full conversation history
- **Verifies order status via Etsy API before responding**
- Extracts order status and product details
- References buyer measurements and preferences

### Automated Order Management
- **Issue refunds automatically** via Etsy API
- **Cancel orders** before they ship
- **Update tracking information**
- Check if order can be cancelled (not yet shipped)

### Policy-Compliant
- Automatically checks if order can be cancelled
- Applies refund window rules
- Sets realistic shipping expectations
- **Never promises refunds for shipped orders**

### Multi-Shop Support
- Configure multiple shops in one file
- Switch between shops with different brand voices
- **Each shop uses its own Chrome profile** (e.g., HazumiCrafts → "Teng" profile)

**Important**: opencli connects to whichever Chrome profile has the extension active. Make sure to open Chrome with the correct profile before using the skill.

See [MULTI_PROFILE_SETUP.md](./MULTI_PROFILE_SETUP.md) for detailed instructions.

## Technical Details

**Powered by**: opencli (browser automation CLI)
**Parser**: Python utilities in `parser.py`
**Config**: YAML-based shop configuration

## Example Workflow

1. User: "Check Etsy messages"
2. Skill opens Etsy Messages via opencli
3. Extracts 3 unread messages:
   - Sarah: sizing inquiry
   - Hayley: refund request (order #4090829817)
4. **Verifies Hayley's order via Etsy API**:
   - Status: Not yet shipped ✅
   - Can cancel: Yes
   - Total: AU$219.00
5. Categorizes each message type
6. Generates reply drafts using shop config
7. Presents drafts with proposed actions:
   - "Issue full refund for order #4090829817"
8. Sends approved replies via opencli
9. **Executes refund via Etsy API** (if approved)
10. Confirms completion to user

## Files

- `skill.yaml`: Skill metadata and triggers
- `prompt.md`: Main instruction prompt with API integration
- `shop_config.yaml`: Shop branding and templates
- `parser.py`: Etsy data parsing utilities (opencli output)
- `etsy_api.py`: **Etsy API v3 client** (orders, refunds, tracking)
- `example.sh`: Usage example script
- `README.md`: This file

## API Usage Examples

### Check Order Status
```bash
python3 etsy_api.py get-order 4090829817
```

### Cancel Order and Issue Refund
```bash
python3 etsy_api.py cancel-order 4090829817
```

### Issue Partial Refund
```bash
python3 etsy_api.py refund 4090829817 50.00
```

### Python API
```python
from etsy_api import EtsyAPIClient

client = EtsyAPIClient()
shop = client.get_shop()

# Get order details
status = client.get_order_status(shop['shop_id'], 4090829817)
print(f"Can cancel: {status['can_cancel']}")

# Issue refund
if status['can_cancel']:
    client.issue_full_refund(shop['shop_id'], 4090829817)
```

## Troubleshooting

### Message Not Sending

**Issue**: Clicked send button but message doesn't appear in conversation thread.

**Solution**:
1. The page has multiple submit buttons. Make sure to use:
   ```bash
   opencli browser cs-session find --role button --text "Send"
   ```
   NOT `--css 'button[type="submit"]'` which may match the wrong button.

2. After clicking send, wait 2-3 seconds and verify:
   ```bash
   sleep 3
   opencli browser cs-session extract
   ```
   Check if your message appears in the thread.

3. If message still doesn't appear, try clicking the Send button again.

### opencli Connection Issues

**Issue**: `opencli doctor` shows extension not connected.

**Solution**:
1. Make sure Chrome is open with the correct profile (e.g., "Teng" for HazumiCrafts)
2. Check that the opencli extension is installed and active
3. Restart Chrome if needed
4. Run `opencli doctor` to verify connection

### Wrong Chrome Profile

**Issue**: Messages from wrong shop appear.

**Solution**:
1. Check `shop_config.yaml` to see which Chrome profile the shop uses
2. Close any existing opencli sessions: `opencli browser cs-session close`
3. Open Chrome with the correct profile
4. Restart the skill workflow

## Future Enhancements

- [x] Automatic order cancellation via Etsy API ✅
- [x] Full refund automation ✅
- [ ] Reply analytics and response time tracking
- [ ] Template A/B testing
- [ ] Saved reply snippets
- [ ] Multi-language support
- [ ] Bulk message processing
- [ ] Auto-respond to common questions (with approval)
