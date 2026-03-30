"""
One-time script to initialize tokens.json with a fresh refresh token.
Run this ONCE before starting the service.

Usage:
    python init_tokens.py --refresh-token "def50200..."
"""

import argparse
import json
import time
from urllib.request import Request, urlopen

from config import AMOCRM_DOMAIN, AMOCRM_CLIENT_ID, AMOCRM_CLIENT_SECRET, AMOCRM_REDIRECT_URI, TOKEN_FILE


def main():
    parser = argparse.ArgumentParser(description="Initialize amoCRM tokens")
    parser.add_argument("--refresh-token", required=True, help="Current refresh token")
    args = parser.parse_args()

    print("Exchanging refresh token for access token...")

    url = f"https://{AMOCRM_DOMAIN}/oauth2/access_token"
    payload = json.dumps({
        "client_id": AMOCRM_CLIENT_ID,
        "client_secret": AMOCRM_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": args.refresh_token,
        "redirect_uri": AMOCRM_REDIRECT_URI,
    }).encode()

    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    tokens = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + data.get("expires_in", 86400) - 300,
    }

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)

    print(f"Tokens saved to {TOKEN_FILE}")
    print(f"Access token expires at: {time.ctime(tokens['expires_at'])}")
    print("Service is ready to start.")


if __name__ == "__main__":
    main()
