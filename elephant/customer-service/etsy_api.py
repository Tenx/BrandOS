#!/usr/bin/env python3
"""
Etsy API Client for Customer Service
Handles receipts, transactions, messages, and refunds
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List


class EtsyAPIClient:
    """Etsy API v3 client with OAuth 2.0"""

    def __init__(self, token_file: str = None):
        """
        Initialize Etsy API client

        Args:
            token_file: Path to .etsy_token.json (default: etsy_publisher/.etsy_token.json)
        """
        if token_file is None:
            # Try to find token file
            possible_paths = [
                Path.home() / ".etsy/etsy_token.json",
                Path(__file__).parent / ".etsy_token.json",
            ]
            for path in possible_paths:
                if path.exists():
                    token_file = str(path)
                    break

        if not token_file or not Path(token_file).exists():
            raise FileNotFoundError(
                "Etsy token file not found. Run oauth flow first:\n"
                "  python3 etsy_publisher/oauth_pkce.py"
            )

        self.token_file = Path(token_file)
        self.token_data = self._load_token()
        self.base_url = "https://api.etsy.com/v3/application"

        # Load API credentials from .env
        self.api_key = None
        self.api_secret = None
        env_paths = [
            Path.home() / ".etsy/.env",
            Path(__file__).parent / ".env",
        ]
        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith('ETSY_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                        elif line.startswith('ETSY_API_SECRET='):
                            self.api_secret = line.split('=', 1)[1].strip()
                break

        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials not found in .env file")

    def _load_token(self) -> Dict:
        """Load access token from file"""
        with open(self.token_file, 'r') as f:
            return json.load(f)

    def _save_token(self, token_data: Dict):
        """Save updated token to file"""
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

    def _refresh_token_if_needed(self):
        """Check token expiry and refresh if needed"""
        expires_at = self.token_data.get('expires_at', 0)
        if time.time() >= expires_at - 300:  # Refresh 5 min before expiry
            print("🔄 Refreshing Etsy access token...")
            self._refresh_access_token()

    def _refresh_access_token(self):
        """Refresh expired access token"""
        if 'refresh_token' not in self.token_data:
            raise Exception("No refresh token available")

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.api_key,
            'refresh_token': self.token_data['refresh_token']
        }

        response = requests.post(
            "https://api.etsy.com/v3/public/oauth/token",
            json=data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            new_token = response.json()
            new_token['expires_at'] = time.time() + new_token.get('expires_in', 3600)
            self.token_data = new_token
            self._save_token(new_token)
            print("✅ Token refreshed")
        else:
            raise Exception(f"Token refresh failed: {response.status_code} {response.text}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated API request"""
        self._refresh_token_if_needed()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f"Bearer {self.token_data['access_token']}",
            'x-api-key': f"{self.api_key}:{self.api_secret}",  # Format: key:secret
            **kwargs.pop('headers', {})
        }

        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} {response.text}")

    # ==================== SHOP INFO ====================

    def get_shop(self, shop_id: str = None) -> Dict:
        """Get shop information"""
        if shop_id is None:
            # Try to load shop_id from etsy_shop_profile.yaml
            profile_paths = [
                Path.home() / ".etsy/etsy_shop_profile.yaml",
                Path(__file__).parent / "etsy_shop_profile.yaml",
            ]
            for profile_path in profile_paths:
                if profile_path.exists():
                    import yaml
                    with open(profile_path) as f:
                        profile = yaml.safe_load(f)
                        shop_id = profile.get('shop', {}).get('shop_id')
                        if shop_id:
                            break

            if not shop_id:
                raise ValueError(
                    "Shop ID not found. Please specify shop_id or add it to etsy_shop_profile.yaml"
                )

        return self._make_request('GET', f'/shops/{shop_id}')

    # ==================== RECEIPTS (ORDERS) ====================

    def get_receipt(self, shop_id: str, receipt_id: int) -> Dict:
        """
        Get order details by receipt ID

        Returns:
            {
                'receipt_id': 123,
                'buyer_email': 'buyer@example.com',
                'name': 'Buyer Name',
                'create_timestamp': 1234567890,
                'shipments': [...],
                'transactions': [...],
                'discount_amt': {...},
                'grandtotal': {...},
                'is_gift': False,
                'status': 'open' | 'completed' | 'cancelled'
            }
        """
        return self._make_request('GET', f'/shops/{shop_id}/receipts/{receipt_id}')

    def get_shop_receipts(
        self,
        shop_id: str,
        limit: int = 25,
        offset: int = 0,
        status: str = None
    ) -> List[Dict]:
        """
        Get all receipts for a shop

        Args:
            status: 'open', 'completed', 'cancelled', 'all' (default: open)
        """
        params = {'limit': limit, 'offset': offset}
        if status:
            params['was_paid'] = 'true'
            params['was_shipped'] = 'true' if status == 'completed' else 'false'

        result = self._make_request('GET', f'/shops/{shop_id}/receipts', params=params)
        return result.get('results', [])

    def find_receipt_by_order_number(self, shop_id: str, order_number: str) -> Optional[Dict]:
        """Find receipt by order number (e.g., #4090829817)"""
        receipt_id = order_number.lstrip('#')
        try:
            return self.get_receipt(shop_id, int(receipt_id))
        except:
            return None

    # ==================== REFUNDS & CANCELLATIONS ====================

    def cancel_receipt(self, shop_id: str, receipt_id: int) -> Dict:
        """
        Cancel an order (only works if not yet shipped)

        Note: Etsy API v3 doesn't have direct cancel endpoint.
        You need to issue a full refund instead.
        """
        return self.issue_full_refund(shop_id, receipt_id)

    def issue_full_refund(self, shop_id: str, receipt_id: int) -> Dict:
        """
        Issue a full refund for an order

        Returns refund details
        """
        # Get receipt to calculate refund amount
        receipt = self.get_receipt(shop_id, receipt_id)
        total = receipt['grandtotal']['amount']
        currency = receipt['grandtotal']['currency_code']

        return self.issue_refund(shop_id, receipt_id, total / 100, currency)

    def issue_refund(
        self,
        shop_id: str,
        receipt_id: int,
        amount: float,
        currency: str = 'USD',
        reason: str = "Buyer requested cancellation"
    ) -> Dict:
        """
        Issue a partial or full refund

        Args:
            amount: Refund amount (in dollars, not cents)
            currency: Currency code (USD, EUR, etc.)
            reason: Reason for refund
        """
        # Etsy API v3 refund endpoint
        # Note: This requires Payment Write scope
        data = {
            'amount': int(amount * 100),  # Convert to cents
            'reason': reason,
            'currency_code': currency
        }

        return self._make_request(
            'POST',
            f'/shops/{shop_id}/receipts/{receipt_id}/refunds',
            json=data
        )

    # ==================== SHIPPING & TRACKING ====================

    def get_receipt_shipments(self, shop_id: str, receipt_id: int) -> List[Dict]:
        """Get shipment tracking for an order"""
        receipt = self.get_receipt(shop_id, receipt_id)
        return receipt.get('shipments', [])

    def update_tracking(
        self,
        shop_id: str,
        receipt_id: int,
        tracking_code: str,
        carrier_name: str
    ) -> Dict:
        """Add or update tracking information"""
        data = {
            'tracking_code': tracking_code,
            'carrier_name': carrier_name
        }

        return self._make_request(
            'POST',
            f'/shops/{shop_id}/receipts/{receipt_id}/tracking',
            json=data
        )

    # ==================== TRANSACTIONS (LINE ITEMS) ====================

    def get_receipt_transactions(self, shop_id: str, receipt_id: int) -> List[Dict]:
        """Get line items for an order"""
        receipt = self.get_receipt(shop_id, receipt_id)
        return receipt.get('transactions', [])

    # ==================== MESSAGES (Limited API) ====================

    def send_message(self, shop_id: str, conversation_id: int, message: str) -> Dict:
        """
        Send a message to a conversation

        Note: Etsy API v3 has limited message support.
        This may require using opencli instead.
        """
        raise NotImplementedError(
            "Etsy API v3 does not support sending messages directly.\n"
            "Use opencli browser automation instead."
        )

    # ==================== HELPER METHODS ====================

    def get_order_status(self, shop_id: str, receipt_id: int) -> Dict:
        """
        Get detailed order status for customer service

        Returns:
            {
                'receipt_id': 123,
                'order_number': '#123',
                'status': 'open' | 'shipped' | 'completed' | 'cancelled',
                'can_cancel': True/False,
                'buyer_name': 'Name',
                'order_date': 'YYYY-MM-DD',
                'items': [...],
                'tracking': [...],
                'total': '100.00 USD'
            }
        """
        receipt = self.get_receipt(shop_id, receipt_id)

        # Determine if order can be cancelled
        can_cancel = receipt.get('was_shipped', False) == False

        return {
            'receipt_id': receipt['receipt_id'],
            'order_number': f"#{receipt['receipt_id']}",
            'status': receipt.get('status', 'unknown'),
            'can_cancel': can_cancel,
            'buyer_name': receipt.get('name', 'Unknown'),
            'buyer_email': receipt.get('buyer_email', ''),
            'order_date': time.strftime('%Y-%m-%d', time.gmtime(receipt['create_timestamp'])),
            'items': [
                {
                    'title': t.get('title', ''),
                    'quantity': t.get('quantity', 1),
                    'price': f"{t['price']['amount'] / 100:.2f} {t['price']['currency_code']}"
                }
                for t in receipt.get('transactions', [])
            ],
            'tracking': receipt.get('shipments', []),
            'total': f"{receipt['grandtotal']['amount'] / 100:.2f} {receipt['grandtotal']['currency_code']}"
        }


# ==================== CLI USAGE ====================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 etsy_api.py get-order <receipt_id>")
        print("  python3 etsy_api.py cancel-order <receipt_id>")
        print("  python3 etsy_api.py refund <receipt_id> <amount>")
        sys.exit(1)

    client = EtsyAPIClient()
    shop = client.get_shop()
    shop_id = shop['shop_id']

    command = sys.argv[1]

    if command == 'get-order':
        receipt_id = int(sys.argv[2])
        status = client.get_order_status(shop_id, receipt_id)
        print(json.dumps(status, indent=2))

    elif command == 'cancel-order':
        receipt_id = int(sys.argv[2])
        print(f"Cancelling order #{receipt_id}...")
        result = client.cancel_receipt(shop_id, receipt_id)
        print("✅ Order cancelled and refund issued")
        print(json.dumps(result, indent=2))

    elif command == 'refund':
        receipt_id = int(sys.argv[2])
        amount = float(sys.argv[3])
        print(f"Issuing refund of ${amount:.2f} for order #{receipt_id}...")
        result = client.issue_refund(shop_id, receipt_id, amount)
        print("✅ Refund issued")
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
