#!/usr/bin/env python3
"""
Regional Distribution — where is this game popular?
Sources:
  1. Google Play multi-country install check (google-play-scraper)
  2. App Store iTunes top charts by country
  3. Web search fallback (Sensor Tower / appfigures public data)
"""
import os, requests, json

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
TAVILY_API_KEY  = os.environ.get("TAVILY_API_KEY", "")

# Countries to probe
PROBE_COUNTRIES = [
    ("us", "🇺🇸 US"), ("br", "🇧🇷 Brazil"), ("id", "🇮🇩 Indonesia"),
    ("vn", "🇻🇳 Vietnam"), ("de", "🇩🇪 Germany"), ("gb", "🇬🇧 UK"),
    ("jp", "🇯🇵 Japan"), ("kr", "🇰🇷 Korea"), ("th", "🇹🇭 Thailand"),
    ("ph", "🇵🇭 Philippines"), ("mx", "🇲🇽 Mexico"), ("in", "🇮🇳 India"),
    ("au", "🇦🇺 Australia"), ("fr", "🇫🇷 France"), ("tr", "🇹🇷 Turkey"),
]

def check_googleplay_countries(bundle_id, countries=None):
    """Check if app is available and get rating in each country."""
    if not bundle_id:
        return {}
    try:
        from google_play_scraper import app as gp_app
    except ImportError:
        return {}

    if countries is None:
        countries = PROBE_COUNTRIES

    results = {}
    for code, label in countries:
        try:
            data = gp_app(bundle_id, lang="en", country=code)
            if data.get("title"):
                results[code] = {
                    "label": label,
                    "available": True,
                    "score": round(data.get("score", 0), 2),
                    "ratings": data.get("ratings", 0),
                    "installs": data.get("installs", ""),
                }
        except Exception:
            pass
    return results

def check_appstore_countries(app_id, countries=None):
    """Check App Store availability and rating by country."""
    if not app_id:
        return {}
    if countries is None:
        countries = PROBE_COUNTRIES

    results = {}
    for code, label in countries:
        try:
            r = requests.get(
                f"https://itunes.apple.com/{code}/lookup",
                params={"id": app_id}, timeout=6
            )
            data = r.json().get("results", [])
            if data:
                d = data[0]
                results[code] = {
                    "label": label,
                    "available": True,
                    "score": round(d.get("averageUserRating", 0), 2),
                    "ratings": d.get("userRatingCount", 0),
                }
        except Exception:
            pass
    return results

def search_download_distribution(game_name):
    """
    Use web search to find public download distribution data.
    Returns raw text summary from Sensor Tower / appfigures public pages.
    """
    if not TAVILY_API_KEY:
        return None
    try:
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": TAVILY_API_KEY,
            "query": f"{game_name} download statistics by country region 2025 2026",
            "max_results": 3,
            "search_depth": "basic",
        }, timeout=10)
        results = r.json().get("results", [])
        snippets = [res.get("content", "") for res in results if res.get("content")]
        return " ".join(snippets)[:800] if snippets else None
    except Exception:
        return None

def analyze_regional_distribution(game_name, bundle_id=None, appstore_id=None, fast=False):
    """
    Main entry: combines GP multi-country + AppStore multi-country + web search.
    fast=True skips multi-country store checks (faster, less accurate).
    """
    result = {
        "game": game_name,
        "googleplay_countries": {},
        "appstore_countries": {},
        "web_summary": None,
    }

    if not fast:
        if bundle_id:
            # Only probe top 8 countries to avoid rate limiting
            result["googleplay_countries"] = check_googleplay_countries(
                bundle_id, PROBE_COUNTRIES[:8]
            )
        if appstore_id:
            result["appstore_countries"] = check_appstore_countries(
                appstore_id, PROBE_COUNTRIES[:8]
            )

    # Always try web search for richer distribution data
    summary = search_download_distribution(game_name)
    result["web_summary"] = summary

    return result

def print_regional_distribution(result):
    gp = result.get("googleplay_countries", {})
    ios = result.get("appstore_countries", {})
    web = result.get("web_summary", "")

    if gp:
        print(f"  🤖 Google Play availability ({len(gp)} countries checked):")
        for code, d in gp.items():
            print(f"     {d['label']:<20} ⭐ {d['score']}  ({d['ratings']:,} ratings)  {d['installs']}")

    if ios:
        print(f"\n  🍎 App Store availability ({len(ios)} countries checked):")
        for code, d in ios.items():
            if d.get("available"):
                print(f"     {d['label']:<20} ⭐ {d['score']}  ({d['ratings']:,} ratings)")

    if web:
        # Extract key country % mentions
        import re
        pct_matches = re.findall(r'([A-Za-z\s]+):\s*(\d+)%', web)
        if pct_matches:
            print(f"\n  🌍 Download distribution (public data):")
            for country, pct in pct_matches[:6]:
                print(f"     {country.strip():<20} {pct}%")
        else:
            print(f"\n  🌍 Regional notes: {web[:300]}")
