#!/usr/bin/env python3
"""
Social Accounts — Official social media presence for a game.
Sources:
  1. YouTube API (subscriber count, verified)
  2. Web search (X/Twitter, Facebook, TikTok, Reddit, Discord follower counts)
  3. games_db.json cache
"""
import os, requests, re, json

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
TAVILY_API_KEY  = os.environ.get("TAVILY_API_KEY", "")
YT_BASE = "https://www.googleapis.com/youtube/v3"

PLATFORMS = ["x.com", "twitter.com", "facebook.com", "tiktok.com",
             "reddit.com", "discord.gg", "instagram.com"]

def get_youtube_channel_stats(channel_id):
    """Get YouTube channel subscriber count and basic stats."""
    if not channel_id or not YOUTUBE_API_KEY:
        return {}
    try:
        r = requests.get(f"{YT_BASE}/channels", params={
            "key": YOUTUBE_API_KEY,
            "id": channel_id,
            "part": "statistics,snippet",
        }, timeout=8)
        items = r.json().get("items", [])
        if not items:
            return {}
        stats = items[0].get("statistics", {})
        snippet = items[0].get("snippet", {})
        subs = int(stats.get("subscriberCount", 0)) if not stats.get("hiddenSubscriberCount") else None
        return {
            "url": f"https://www.youtube.com/channel/{channel_id}",
            "handle": snippet.get("customUrl", ""),
            "subscribers": subs,
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }
    except Exception:
        return {}

def search_social_accounts(game_name):
    """
    Web search for official social accounts across platforms.
    Returns dict of platform -> {url, followers (if found)}.
    """
    if not TAVILY_API_KEY:
        return {}

    platforms_query = " OR ".join([f"site:{p}" for p in PLATFORMS])
    query = f'"{game_name}" official {platforms_query} followers'

    try:
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": 5,
            "search_depth": "basic",
            "include_domains": ["x.com", "twitter.com", "facebook.com",
                               "tiktok.com", "reddit.com", "instagram.com",
                               "twstalker.com", "trackalytics.com"],
        }, timeout=10)
        results = r.json().get("results", [])
    except Exception:
        return {}

    accounts = {}
    game_lower = game_name.lower().replace(" ", "").replace(":", "")

    for res in results:
        url = res.get("url", "").lower()
        content = res.get("content", "")

        # X/Twitter
        if "twitter.com" in url or "x.com" in url or "twstalker.com" in url:
            m = re.search(r'(\d[\d,]+)\s*follower', content, re.I)
            handle_m = re.search(r'(?:twitter\.com|x\.com)/(@?[\w]+)', url)
            handle = handle_m.group(1) if handle_m else ""
            if not handle or "twstalker" in url:
                handle_m2 = re.search(r'@([\w]+)', content)
                handle = f"@{handle_m2.group(1)}" if handle_m2 else ""
            accounts["twitter_x"] = {
                "url": f"https://x.com/{handle.lstrip('@')}" if handle else "",
                "handle": handle,
                "followers": int(m.group(1).replace(",", "")) if m else None,
                "source": res.get("url"),
            }

        # Reddit
        elif "reddit.com/r/" in url:
            m = re.search(r'(\d[\d,]+)\s*member', content, re.I)
            sub_m = re.search(r'reddit\.com/r/([\w]+)', url)
            subreddit = sub_m.group(1) if sub_m else ""
            if subreddit:
                accounts["reddit"] = {
                    "url": f"https://reddit.com/r/{subreddit}",
                    "subreddit": f"r/{subreddit}",
                    "members": int(m.group(1).replace(",", "")) if m else None,
                }

        # Facebook
        elif "facebook.com" in url:
            m = re.search(r'(\d[\d,]+)\s*(?:follower|like|fan)', content, re.I)
            accounts["facebook"] = {
                "url": res.get("url", ""),
                "followers": int(m.group(1).replace(",", "")) if m else None,
            }

        # TikTok
        elif "tiktok.com" in url:
            m = re.search(r'(\d[\d,.]+[KMB]?)\s*follower', content, re.I)
            accounts["tiktok"] = {
                "url": res.get("url", ""),
                "followers_raw": m.group(1) if m else None,
            }

        # Instagram
        elif "instagram.com" in url:
            m = re.search(r'(\d[\d,]+)\s*follower', content, re.I)
            accounts["instagram"] = {
                "url": res.get("url", ""),
                "followers": int(m.group(1).replace(",", "")) if m else None,
            }

    return accounts

def get_all_social_accounts(game_name, yt_channel_id=None, db_accounts=None):
    """
    Combine: YouTube API + web search + db cache.
    db_accounts: dict from games_db.json official_accounts field.
    """
    result = {}

    # YouTube (API — most reliable)
    if yt_channel_id:
        yt = get_youtube_channel_stats(yt_channel_id)
        if yt:
            result["youtube"] = yt
    elif db_accounts and db_accounts.get("youtube_channel_id"):
        yt = get_youtube_channel_stats(db_accounts["youtube_channel_id"])
        if yt:
            result["youtube"] = yt

    # Other platforms via web search
    searched = search_social_accounts(game_name)
    result.update(searched)

    # Fill in any URLs already known from db
    if db_accounts:
        for key, val in db_accounts.items():
            if key == "youtube_channel_id":
                continue
            if key not in result and val:
                result[key] = {"url": val, "followers": None}

    return result

def fmt_num(n):
    if n is None: return "?"
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def print_social_accounts(accounts):
    platform_labels = {
        "youtube":   "▶️  YouTube",
        "twitter_x": "🐦 X/Twitter",
        "facebook":  "📘 Facebook",
        "tiktok":    "🎵 TikTok",
        "instagram": "📷 Instagram",
        "reddit":    "🔴 Reddit",
        "discord":   "💬 Discord",
    }
    for platform, label in platform_labels.items():
        if platform not in accounts:
            continue
        info = accounts[platform]
        url  = info.get("url") or info.get("handle") or ""
        if platform == "youtube":
            subs = fmt_num(info.get("subscribers"))
            handle = info.get("handle", "")
            print(f"  {label:<20} {url}")
            print(f"  {'':20} {subs} subscribers · {fmt_num(info.get('video_count'))} videos")
        elif platform == "twitter_x":
            followers = fmt_num(info.get("followers"))
            handle = info.get("handle", "")
            print(f"  {label:<20} {url}  [{followers} followers]")
        elif platform == "reddit":
            members = fmt_num(info.get("members"))
            sub = info.get("subreddit", "")
            print(f"  {label:<20} {url}  [{members} members]")
        elif platform == "facebook":
            followers = fmt_num(info.get("followers"))
            print(f"  {label:<20} {url}  [{followers} followers]")
        elif platform == "tiktok":
            followers = info.get("followers_raw") or fmt_num(info.get("followers"))
            print(f"  {label:<20} {url}  [{followers} followers]")
        else:
            print(f"  {label:<20} {url}")
