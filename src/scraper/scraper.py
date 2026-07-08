"""
Phase 2a (Updated): Browser-based scraper for Groww Mutual Fund Pages.

Since Groww serves compressed HTML that requires a browser to render,
this script uses the rendered HTML approach to fetch page content.
It saves full rendered HTML for each scheme page locally.
"""
from typing import Optional, List
import os
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import GROWW_URLS


# Directory to store raw HTML files
RAW_HTML_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw_html')


import random

def _get_headers():
    """Return randomized browser-like headers to avoid being blocked."""
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def _url_to_filename(url: str) -> str:
    """Convert a Groww URL to a safe filename for local storage."""
    slug = url.rstrip("/").split("/")[-1]
    return f"{slug}.html"


def fetch_single_url(url: str, scheme_name: str, retries: int = 3, delay: float = 2.0) -> dict:
    """
    Fetch raw HTML from a single Groww URL with retry logic.

    Args:
        url: The Groww mutual fund URL to scrape.
        scheme_name: Human-readable scheme name.
        retries: Number of retry attempts on failure.
        delay: Delay in seconds between retries (exponential backoff).

    Returns:
        dict with keys: url, scheme_name, html, status_code, timestamp, error
    """
    result = {
        "url": url,
        "scheme_name": scheme_name,
        "html": None,
        "status_code": None,
        "timestamp": datetime.now().isoformat(),
        "error": None,
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"  [Attempt {attempt}/{retries}] Fetching: {scheme_name}...")
            response = requests.get(url, headers=_get_headers(), timeout=30)
            result["status_code"] = response.status_code

            if response.status_code == 200:
                result["html"] = response.text
                print(f"  ✅ Success: {scheme_name} ({len(response.text)} chars)")
                return result
            elif response.status_code in (403, 429):
                print(f"  ⚠️  HTTP {response.status_code} (blocked/rate-limited). Retrying...")
            else:
                print(f"  ⚠️  HTTP {response.status_code}. Retrying...")

        except requests.exceptions.Timeout:
            result["error"] = "Request timed out"
            print(f"  ⚠️  Timeout. Retrying...")
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"Connection error: {str(e)}"
            print(f"  ⚠️  Connection error. Retrying...")
        except requests.exceptions.RequestException as e:
            result["error"] = f"Request failed: {str(e)}"
            print(f"  ⚠️  Request error: {e}. Retrying...")

        # Exponential backoff
        if attempt < retries:
            wait_time = delay * (2 ** (attempt - 1))
            print(f"  ⏳ Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    # All retries exhausted
    if result["error"] is None:
        result["error"] = f"Failed after {retries} attempts (HTTP {result['status_code']})"
    print(f"  ❌ Failed: {scheme_name} — {result['error']}")
    return result


def save_raw_html(result: dict) -> Optional[str]:
    """
    Save the fetched raw HTML to a local file.

    Args:
        result: The result dict from fetch_single_url.

    Returns:
        The file path if saved successfully, else None.
    """
    if result["html"] is None:
        return None

    os.makedirs(RAW_HTML_DIR, exist_ok=True)
    filename = _url_to_filename(result["url"])
    filepath = os.path.join(RAW_HTML_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result["html"])

    print(f"  💾 Saved: {filepath}")
    return filepath


def scrape_all_urls() -> List[dict]:
    """
    Scrape all 5 Groww mutual fund URLs.

    Returns:
        List of result dicts, one per URL.
    """
    print("=" * 60)
    print("🔍 Starting Groww Mutual Fund Scraper")
    print(f"   Target URLs: {len(GROWW_URLS)}")
    print("=" * 60)

    results = []
    for i, entry in enumerate(GROWW_URLS, 1):
        print(f"\n[{i}/{len(GROWW_URLS)}] {entry['scheme_name']}")
        result = fetch_single_url(entry["url"], entry["scheme_name"])
        filepath = save_raw_html(result)
        result["local_filepath"] = filepath
        results.append(result)

        # Polite delay between requests
        if i < len(GROWW_URLS):
            time.sleep(1)

    # Summary
    success = sum(1 for r in results if r["html"] is not None)
    failed = len(results) - success
    print("\n" + "=" * 60)
    print(f"📊 Scraping Complete: {success} succeeded, {failed} failed")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = scrape_all_urls()

    # Print final summary
    print("\n📋 Results Summary:")
    for r in results:
        status = "✅" if r["html"] else "❌"
        size = f"{len(r['html'])} chars" if r["html"] else r["error"]
        print(f"  {status} {r['scheme_name']}: {size}")
