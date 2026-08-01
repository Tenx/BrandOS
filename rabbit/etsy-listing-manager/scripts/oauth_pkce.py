#!/usr/bin/env python3
"""
Etsy OAuth 2.0 with PKCE - Python Implementation
Based on Etsy's official Quick Start Tutorial
"""

import sys
import json
import requests
import base64
import hashlib
import secrets
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import parse_qs, urlparse

from etsy_profile import api_credentials, consume_profile_arg, load_profile, project_path

PROFILE = load_profile(consume_profile_arg(sys.argv))
REDIRECT_URI = PROFILE["etsy_api"].get("redirect_uri", "http://localhost:8080/oauth/redirect")
SCOPES = PROFILE["etsy_api"].get("scopes", "listings_w listings_r shops_r shops_w transactions_r")
TOKEN_FILE = project_path("token_file", profile=PROFILE)
STATE_FILE = TOKEN_FILE.parent / ".oauth_state.json"
API_KEY = None
API_SECRET = None

# Etsy API endpoints
AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"

# Global state
oauth_state = {}


def require_api_credentials():
    global API_KEY, API_SECRET
    if not API_KEY or not API_SECRET:
        API_KEY, API_SECRET = api_credentials(PROFILE)
    return API_KEY, API_SECRET


def base64_url_encode(data):
    """Base64 URL encode without padding"""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    # Generate code verifier (random 32 bytes)
    code_verifier = base64_url_encode(secrets.token_bytes(32))

    # Generate code challenge (SHA256 hash of verifier)
    challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64_url_encode(challenge)

    return code_verifier, code_challenge


def generate_state():
    """Generate random state string"""
    return secrets.token_urlsafe(16)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth callback from Etsy"""

    def do_GET(self):
        """Handle the OAuth callback"""
        global oauth_state

        query = parse_qs(urlparse(self.path).query)

        if 'code' in query:
            oauth_state['auth_code'] = query['code'][0]
            oauth_state['state_received'] = query.get('state', [''])[0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_response = """
                <html>
                <head>
                    <title>Authorization Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #28a745; }
                        p { font-size: 18px; }
                    </style>
                </head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    <p>Your Etsy app is now authorized.</p>
                </body>
                </html>
            """
            self.wfile.write(html_response.encode('utf-8'))
        else:
            oauth_state['error'] = query.get('error', ['Unknown error'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_response = """
                <html>
                <head>
                    <title>Authorization Failed</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #dc3545; }
                    </style>
                </head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Please try again.</p>
                </body>
                </html>
            """
            self.wfile.write(html_response.encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress logging"""
        pass


def start_oauth_flow():
    """Start OAuth 2.0 PKCE flow"""
    global oauth_state

    print("\n🔐 Starting OAuth 2.0 Authorization Flow with PKCE...")
    api_key, _api_secret = require_api_credentials()

    # Generate PKCE pair and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()

    # Save state and verifier for later
    oauth_state = {
        'code_verifier': code_verifier,
        'state_sent': state,
        'auth_code': None,
        'error': None
    }

    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(oauth_state, f, indent=2)

    print(f"✅ Generated PKCE challenge")
    print(f"✅ Generated state: {state[:10]}...")

    # Build authorization URL
    params = {
        'response_type': 'code',
        'client_id': api_key,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }

    from urllib.parse import urlencode
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print(f"\n📖 Opening browser for authorization...")
    print(f"\nIf browser doesn't open automatically, visit:")
    print(f"{auth_url}\n")

    # Start local server on port 8080
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server_thread = Thread(target=server.handle_request)
    server_thread.start()

    print("⏳ Starting local server on port 8080...")
    print("⏳ Waiting for authorization...\n")

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback (timeout 180 seconds)
    server_thread.join(timeout=180)

    # Check if we got the auth code
    if oauth_state.get('auth_code'):
        print("✅ Authorization code received!")

        # Verify state matches
        if oauth_state['state_sent'] != oauth_state['state_received']:
            print("❌ State mismatch! Possible CSRF attack.")
            sys.exit(1)

        return oauth_state['auth_code'], code_verifier
    elif oauth_state.get('error'):
        print(f"❌ Authorization error: {oauth_state['error']}")
        sys.exit(1)
    else:
        print("❌ Authorization timed out")
        print("\nPlease make sure:")
        print("1. You clicked 'Allow Access' on the Etsy page")
        print("2. The callback URL in your app settings is: http://localhost:8080/oauth/redirect")
        print("3. Port 8080 is not blocked by firewall")
        sys.exit(1)


def exchange_code_for_token(auth_code, code_verifier):
    """Exchange authorization code for access token using PKCE"""
    print("\n🔄 Exchanging authorization code for access token...")
    api_key, _api_secret = require_api_credentials()

    data = {
        'grant_type': 'authorization_code',
        'client_id': api_key,
        'redirect_uri': REDIRECT_URI,
        'code': auth_code,
        'code_verifier': code_verifier
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(TOKEN_URL, json=data, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        print("✅ Access token received!")
        print(f"   Token type: {token_data.get('token_type')}")
        print(f"   Expires in: {token_data.get('expires_in')} seconds")
        print(f"   Refresh token: {'Yes' if token_data.get('refresh_token') else 'No'}")

        # Save token
        import time
        token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)

        TOKEN_FILE.parent.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

        print(f"\n💾 Token saved to: {TOKEN_FILE}")

        # Clean up state file
        if STATE_FILE.exists():
            STATE_FILE.unlink()

        return token_data
    else:
        print(f"❌ Token exchange failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)


def refresh_access_token():
    """Refresh expired access token"""
    if not TOKEN_FILE.exists():
        print("❌ No token file found")
        return None

    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    if 'refresh_token' not in token_data:
        print("❌ No refresh token available")
        return None

    print("\n🔄 Refreshing access token...")
    api_key, _api_secret = require_api_credentials()

    data = {
        'grant_type': 'refresh_token',
        'client_id': api_key,
        'refresh_token': token_data['refresh_token']
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(TOKEN_URL, json=data, headers=headers)

    if response.status_code == 200:
        new_token_data = response.json()
        print("✅ Token refreshed!")

        import time
        new_token_data['expires_at'] = time.time() + new_token_data.get('expires_in', 3600)

        with open(TOKEN_FILE, 'w') as f:
            json.dump(new_token_data, f, indent=2)

        return new_token_data
    else:
        print(f"❌ Token refresh failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ETSY OAUTH 2.0 WITH PKCE AUTHORIZATION")
    print("="*60)

    # Start OAuth flow
    auth_code, code_verifier = start_oauth_flow()

    # Exchange code for token
    token_data = exchange_code_for_token(auth_code, code_verifier)

    print("\n" + "="*60)
    print("✅ AUTHORIZATION COMPLETE!")
    print("="*60)
    print("\nYou can now publish listings to Etsy:")
    print("  python3 publish_to_etsy.py --listing 'rose cardigan' --price 52")
    print("\n")
