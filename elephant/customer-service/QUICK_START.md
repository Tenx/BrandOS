# Quick Start Guide - Etsy Customer Service Skill

## 🚀 5-Minute Setup

### 0. Verify Chrome Profile (IMPORTANT)

**For HazumiCrafts, use Chrome profile "Teng"**

```bash
# Quick check
~/.codex/skills/etsy-customer-service/check_profile.sh

# Or manual check
opencli doctor
# Should show: Profile connected
```

If wrong profile is active:
1. Close current Chrome profile
2. Open Chrome with "Teng" profile
3. Verify with script above

### 1. Prerequisites Check
```bash
# Check opencli
opencli doctor
# Should show: ✅ connected

# Check Etsy token
cat /Users/I742076/.claude/projects/hazumi/etsy_publisher/.etsy_token.json
# If missing, run: python3 etsy_publisher/oauth_pkce.py
```

### 2. Test the Skill
```bash
cd ~/.codex/skills/etsy-customer-service
python3 test_integration.py
```

Expected output:
```
✅ Etsy API: Connected
✅ Order Management: Working
✅ Message Parser: Working
✅ Refund System: Ready
```

### 3. Use in Claude Code

**Check messages:**
```
Check my Etsy messages
```

**Reply to unread:**
```
Reply to my unread Etsy messages
```

---

## 💡 Example Commands

### Via CLI
```bash
# Get order status
python3 etsy_api.py get-order 4090829817

# Cancel order and refund
python3 etsy_api.py cancel-order 4090829817

# Issue partial refund
python3 etsy_api.py refund 4090829817 50.00
```

### Via Claude Code
```
"Cancel Etsy order #4090829817"
"Check if order #4090829817 can be refunded"
"Get tracking for order #4090829817"
```

---

## 🔧 Troubleshooting

### Problem: "Shop ID not found"
**Solution:** Shop ID is loaded from `etsy_shop_profile.yaml`. It's already configured for HazumiCrafts (20691319).

### Problem: "Token expired"
**Solution:**
```bash
cd /Users/I742076/.claude/projects/hazumi
python3 etsy_publisher/oauth_pkce.py
```

### Problem: "Cannot cancel order"
**Reason:** Order has already shipped.
**Check:**
```bash
python3 etsy_api.py get-order ORDER_NUMBER
# Look for "can_cancel": true/false
```

---

## 📖 Full Documentation

- [API_INTEGRATION_COMPLETE.md](./API_INTEGRATION_COMPLETE.md) - Detailed integration guide
- [README.md](./README.md) - Feature overview
- [prompt.md](./prompt.md) - Skill instructions

---

## ✨ What You Can Do Now

1. **Read messages** from Etsy Messages inbox (opencli)
2. **Verify order status** before promising refunds (Etsy API)
3. **Issue refunds automatically** with one approval (Etsy API)
4. **Cancel orders** before they ship (Etsy API)
5. **Send professional replies** based on your brand voice (opencli)

---

## 🎯 Next Steps

1. Customize `shop_config.yaml` with your brand voice
2. Try replying to a real customer message
3. Test the refund workflow with a test order (if available)

Ready to use! 🚀
