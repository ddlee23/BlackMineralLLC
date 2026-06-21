#!/usr/bin/env python3
"""
Fetch latest trading-card listings (e.g. "pokemon cards") from eBay Browse API
and write results to an Excel spreadsheet.

Usage:
        - Set EBAY_ACCESS_TOKEN env var (OAuth App access token) or EBAY_USER_TOKEN (user token)
        - Optionally set EBAY_ENV=production|sandbox (default: production)
        - Provide optional eBay App/Dev/Cert IDs via env vars: EBAY_APP_ID, EBAY_DEV_ID, EBAY_CERT_ID
        - Run: python3 ebayapi.py --query "pokemon card" --limit 100
"""

import os
import sys
import argparse
import requests
import math
# Optional: load .env file when present (for local development)
try:
        from dotenv import load_dotenv
        load_dotenv()
except Exception:
        # dotenv not installed or .env not present; continue reading from environment
        pass

try:
        import pandas as pd
except Exception:
        print("This script requires pandas (and openpyxl for Excel output). Install via pip.", file=sys.stderr)
        sys.exit(1)

EBAY_ENV = os.getenv("EBAY_ENV", "production").lower()
# Primary token used for API requests. Prefer EBAY_ACCESS_TOKEN (OAuth), fallback to EBAY_USER_TOKEN,
# and finally the hardcoded token below if neither environment variable is set.
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_DEV_ID = os.getenv("EBAY_DEV_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
EBAY_USER_TOKEN = os.getenv("EBAY_USER_TOKEN")
DEFAULT_EBAY_ACCESS_TOKEN = "v^1.1#i^1#p^3#r^1#f^0#I^3#t^Ul4xMF83OkU4OEY5RkUzMjVDRUZBQzMwNjZEODNCQUEyRTEwMDMzXzJfMSNFXjEyODQ="
ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN") or EBAY_USER_TOKEN or DEFAULT_EBAY_ACCESS_TOKEN
if not ACCESS_TOKEN:
        print("Missing access token. Set EBAY_ACCESS_TOKEN or EBAY_USER_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

# Debug/log of which credential pieces are present (do not print tokens themselves)
loaded = {
        "EBAY_APP_ID": bool(EBAY_APP_ID),
        "EBAY_DEV_ID": bool(EBAY_DEV_ID),
        "EBAY_CERT_ID": bool(EBAY_CERT_ID),
        "EBAY_USER_TOKEN": bool(EBAY_USER_TOKEN),
        "EBAY_ACCESS_TOKEN": bool(os.getenv("EBAY_ACCESS_TOKEN")),
}
print("eBay credential flags:", loaded)

BASE_URL = "https://api.ebay.com" if EBAY_ENV == "production" else "https://api.sandbox.ebay.com"

session = requests.Session()
session.headers.update({
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",  # adjust if needed
})

def search_items(query, category_id=None, limit=50, offset=0):
        """
        Uses Buy Browse API: GET /buy/browse/v1/item_summary/search
        Returns list of item summary dicts.
        """
        url = f"{BASE_URL}/buy/browse/v1/item_summary/search"
        params = {"q": query, "limit": str(limit), "offset": str(offset)}
        if category_id:
                params["category_ids"] = str(category_id)

        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

def extract_items(summary_json):
        items = []
        for it in summary_json.get("itemSummaries", []):
                price = it.get("price", {})
                shipping_options = it.get("shippingOptions", [])
                seller = it.get("seller", {}) or {}
                items.append({
                        "itemId": it.get("itemId"),
                        "title": it.get("title"),
                        "price": price.get("value"),
                        "currency": price.get("currency"),
                        "condition": it.get("condition"),
                        "categoryId": it.get("categoryId"),
                        "categoryPath": it.get("categoryPath"),
                        "itemWebUrl": it.get("itemWebUrl"),
                        "seller_username": seller.get("username"),
                        "seller_feedback_percentage": seller.get("feedbackPercentage"),
                        "shippingType": shipping_options[0].get("shippingType") if shipping_options else None,
                        "shippingCost": shipping_options[0].get("shippingCost", {}).get("value") if shipping_options else None,
                        "availability": it.get("availability", {}).get("pickupAtLocationAvailability") or it.get("availability", {}).get("shipToLocationAvailability"),
                })
        return items

def fetch_all(query, category_id=None, total_limit=200, page_size=50):
        collected = []
        offset = 0
        while len(collected) < total_limit:
                batch_size = min(page_size, total_limit - len(collected))
                data = search_items(query, category_id=category_id, limit=batch_size, offset=offset)
                items = extract_items(data)
                if not items:
                        break
                collected.extend(items)
                offset += len(items)
                # If response told total, we could stop earlier
                total = data.get("total", None)
                if total is not None and offset >= total:
                        break
        return collected

def to_excel(items, filename="ebay_trading_cards.xlsx"):
        df = pd.DataFrame(items)
        # Simple cleanup: ensure consistent column order
        cols = ["itemId", "title", "price", "currency", "condition", "categoryId", "categoryPath", "itemWebUrl",
                        "seller_username", "seller_feedback_percentage", "shippingType", "shippingCost", "availability"]
        cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
        df = df[cols]
        df.to_excel(filename, index=False, engine="openpyxl")
        return filename

def main():
        parser = argparse.ArgumentParser(description="Export eBay trading-card listings to Excel.")
        parser.add_argument("--query", "-q", default="pokemon card", help="Search query (default: 'pokemon card').")
        parser.add_argument("--category", "-c", help="eBay category ID (optional).")
        parser.add_argument("--limit", "-n", type=int, default=200, help="Max number of items to fetch (default:200).")
        parser.add_argument("--page-size", type=int, default=50, help="Items per request (default:50).")
        parser.add_argument("--out", "-o", default="ebay_trading_cards.xlsx", help="Output Excel filename.")
        args = parser.parse_args()

        items = fetch_all(args.query, category_id=args.category, total_limit=args.limit, page_size=args.page_size)
        if not items:
                print("No items found.", file=sys.stderr)
                sys.exit(1)

        out = to_excel(items, filename=args.out)
        print(out)

if __name__ == "__main__":
        main()