#!/usr/bin/env python3
"""
Auto-discover official accounts for any game.
Uses YouTube API + web search to find official channels/handles.
Results can be saved back to games_db.json as verified cache.
"""
import os, requests, json, sys, re, argparse
from pathlib import Path

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"
DB_PATH = Path(__file__).parent.parent / "games_db.json"

# ─── YOUTUBE CHANNEL DISCOVERY ─────────────────────────────────────

def find_youtube_channel(game_name):
    """Search YouTube for the official channel of a game."""
    if not YOUTUBE_API_KEY:
        return None, None
    queries = [
        f"{game_name} official",
        f"{game_name} game official channel",
        game_name,
    ]
    for query in queries:
        try:
            r = requests.get(f"{YOUTUBE_BASE}/search", params={
                "key": YOUTUBE_API_KEY, "q": query, "part": "snippet",
                "type": "channel", "maxResults": 5
            }, timeout=10)
            items = r.json().get("items", [])
            for item in items:
                title = item["snippet"]["channelTitle"].lower()
                gname = game_name.lower()
                # Prioritize channels whose name closely matches the game name
                if (gname in title or
                    all(w in title for w in gname.split() if len(w) > 3)):
                    channel_id = item["snippet"]["channelId"]
                    channel_name = item["snippet"]["channelTitle"]
                    url = f"https://www.youtube.com/channel/{channel_id}"
                    return channel_id, url
        except:
            continue
    return None, None

# ─── WEB SEARCH DISCOVERY ──────────────────────────────────────────

def search_official_accounts(game_name):
    """Use web search to find official social accounts."""
    accounts = {}
    platforms = {
        "twitter_x": f'"{game_name}" official site:x.com OR site:twitter.com',
        "tiktok":    f'"{game_name}" official site:tiktok.com',
        "instagram": f'"{game_name}" official site:instagram.com',
        "reddit":    f'"{game_name}" subreddit site:reddit.com',
    }
    for platform, query in platforms.items():
        try:
            r = requests.get("https://api.tavily.com/search", json={
                "api_key": os.environ.get("TAVILY_API_KEY", ""),
                "query": query,
                "max_results": 3,
                "search_depth": "basic",
            }, timeout=10)
            if r.status_code == 200:
                results = r.json().get("results", [])
                for res in results:
                    url = res.get("url", "")
                    if platform == "twitter_x" and ("x.com/" in url or "twitter.com/" in url):
                        # Filter out search pages, get profile URLs
                        if re.search(r'(x\.com|twitter\.com)/[A-Za-z0-9_]+$', url):
                            accounts[platform] = url
                            break
                    elif platform == "tiktok" and "tiktok.com/@" in url:
                        accounts[platform] = url
                        break
                    elif platform == "instagram" and "instagram.com/" in url:
                        if re.search(r'instagram\.com/[A-Za-z0-9_.]+/?$', url):
                            accounts[platform] = url
                            break
                    elif platform == "reddit" and "reddit.com/r/" in url:
                        m = re.search(r'reddit\.com/r/([A-Za-z0-9_]+)', url)
                        if m:
                            accounts["reddit_subreddit"] = m.group(1)
                            accounts["reddit"] = url
                            break
        except:
            continue
    return accounts

# ─── GOOGLE PLAY BUNDLE DISCOVERY ──────────────────────────────────

def find_google_play_bundle(game_name):
    """Find Google Play bundle ID by searching."""
    try:
        from google_play_scraper import search
        results = search(game_name, n_hits=3, lang="en", country="us")
        if results:
            # Pick the one with highest installs
            best = max(results, key=lambda x: x.get("realInstalls", 0))
            return best.get("appId")
    except:
        pass
    return None

# ─── APP STORE ID DISCOVERY ────────────────────────────────────────

def find_appstore_bundle(game_name):
    """Find App Store app ID by searching iTunes API."""
    try:
        r = requests.get("https://itunes.apple.com/search", params={
            "term": game_name, "country": "us",
            "media": "software", "limit": 3
        }, timeout=10)
        results = r.json().get("results", [])
        if results:
            return results[0].get("trackId"), results[0].get("bundleId")
    except:
        pass
    return None, None

# ─── TAPTAP DISCOVERY ──────────────────────────────────────────────

def find_taptap_id(game_name):
    """Find TapTap game ID by searching."""
    headers = {
        "User-Agent": "TapTap/2.21.0-gplay (Android; 12)",
        "X-UA": "V=1&PN=TapTap&VN_CODE=2210200&VN=2.21.0&LANG=en_US&CH=default&UID=0",
    }
    try:
        r = requests.get("https://www.taptap.io/webapiv2/search/v1/result",
            params={"q": game_name, "type": "app", "page_size": 3},
            headers=headers, timeout=10)
        hits = r.json().get("data", {}).get("hits", {}).get("list", [])
        if hits:
            return str(hits[0].get("app", {}).get("id"))
    except:
        pass
    return None

# ─── MAIN DISCOVER FUNCTION ────────────────────────────────────────

def discover_game(game_name, save_to_db=False, verbose=True):
    """Discover all official accounts for a game."""
    if verbose:
        print(f"\n🔍 Discovering accounts for: {game_name}")
        print("─" * 50)

    result = {
        "steam_id": None,
        "google_play_bundle": None,
        "taptap_id": None,
        "reddit": None,
        "official_accounts": {},
        "youtube_query": game_name,
        "tiktok_hashtag": game_name.lower().replace(" ", "").replace(":", ""),
        "_discovered": True,
        "_confidence": "auto-discovered (verify before use)",
    }

    # YouTube
    if verbose: print("  ▶️  Searching YouTube channel...")
    yt_id, yt_url = find_youtube_channel(game_name)
    if yt_id:
        result["official_accounts"]["youtube_channel_id"] = yt_id
        result["official_accounts"]["youtube"] = f"https://www.youtube.com/channel/{yt_id}"
        if verbose: print(f"     ✅ Found: {yt_url}")
    else:
        if verbose: print(f"     ⚠️  Not found")

    # Google Play
    if verbose: print("  🤖 Searching Google Play...")
    bundle = find_google_play_bundle(game_name)
    if bundle:
        result["google_play_bundle"] = bundle
        if verbose: print(f"     ✅ Bundle: {bundle}")
    else:
        if verbose: print(f"     ⚠️  Not found")

    # App Store
    if verbose: print("  🍎 Searching App Store...")
    _, bundle_id = find_appstore_bundle(game_name)
    if bundle_id:
        result["official_accounts"]["appstore_bundle"] = bundle_id
        if verbose: print(f"     ✅ Bundle: {bundle_id}")
    else:
        if verbose: print(f"     ⚠️  Not found")

    # TapTap
    if verbose: print("  🟢 Searching TapTap...")
    tt_id = find_taptap_id(game_name)
    if tt_id:
        result["taptap_id"] = tt_id
        if verbose: print(f"     ✅ ID: {tt_id}")
    else:
        if verbose: print(f"     ⚠️  Not found")

    # Social accounts via Tavily
    if os.environ.get("TAVILY_API_KEY"):
        if verbose: print("  🌐 Searching social accounts...")
        social = search_official_accounts(game_name)
        if social:
            result["official_accounts"].update(social)
            if social.get("reddit_subreddit"):
                result["reddit"] = social["reddit_subreddit"]
            for k, v in social.items():
                if k != "reddit_subreddit" and verbose:
                    print(f"     ✅ {k}: {v}")
    else:
        if verbose: print("  ⚠️  TAVILY_API_KEY not set — skipping social search")

    # Save to DB
    if save_to_db:
        db = {}
        if DB_PATH.exists():
            db = json.loads(DB_PATH.read_text())
        db[game_name] = {k: v for k, v in result.items()
                         if not k.startswith("_")}
        DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False))
        if verbose:
            print(f"\n  💾 Saved to games_db.json as '{game_name}'")

    if verbose:
        print(f"\n  📋 Summary:")
        for k, v in result.items():
            if k.startswith("_"): continue
            if isinstance(v, dict):
                for sk, sv in v.items():
                    if sv: print(f"     {sk}: {sv}")
            elif v:
                print(f"     {k}: {v}")

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-discover official game accounts")
    parser.add_argument("game", help="Game name to search for")
    parser.add_argument("--save", action="store_true", help="Save results to games_db.json")
    args = parser.parse_args()
    result = discover_game(args.game, save_to_db=args.save)
    if args.save:
        print(f"\nRun benchmark with:\n  python3 benchmark_all.py --game \"{args.game}\" --db-game \"{args.game}\"")
