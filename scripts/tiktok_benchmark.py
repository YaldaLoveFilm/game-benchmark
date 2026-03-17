#!/usr/bin/env python3
"""TikTok benchmark — TikTok unofficial hashtag stats (no key required)"""
import requests, json, sys, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Referer": "https://www.tiktok.com/",
}

def get_tiktok_hashtag(tag):
    """Fetch TikTok hashtag stats via TikTok research API fallback"""
    tag = tag.lstrip("#")
    # Method 1: TikTok challenge page (public)
    url = f"https://www.tiktok.com/api/challenge/detail/?challengeName={tag}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            challenge = data.get("challengeInfo", {}).get("challenge", {})
            stats = data.get("challengeInfo", {}).get("stats", {})
            if challenge:
                return {
                    "platform": "TikTok",
                    "hashtag": f"#{tag}",
                    "video_count": stats.get("videoCount"),
                    "view_count": stats.get("viewCount"),
                    "view_count_str": _fmt(stats.get("viewCount")),
                    "challenge_id": challenge.get("id"),
                    "url": f"https://www.tiktok.com/tag/{tag}",
                }
    except:
        pass

    # Method 2: Scrape meta tags from tag page
    try:
        r = requests.get(f"https://www.tiktok.com/tag/{tag}", headers=HEADERS, timeout=10)
        views_match = re.search(r'"viewCount":(\d+)', r.text)
        videos_match = re.search(r'"videoCount":(\d+)', r.text)
        if views_match:
            views = int(views_match.group(1))
            videos = int(videos_match.group(1)) if videos_match else None
            return {
                "platform": "TikTok",
                "hashtag": f"#{tag}",
                "video_count": videos,
                "view_count": views,
                "view_count_str": _fmt(views),
                "url": f"https://www.tiktok.com/tag/{tag}",
                "note": "scraped from page meta"
            }
    except:
        pass

    return {
        "platform": "TikTok",
        "hashtag": f"#{tag}",
        "error": "Could not retrieve data — TikTok may be blocking requests. Try with a browser or cookie injection.",
        "url": f"https://www.tiktok.com/tag/{tag}",
    }

def _fmt(n):
    if not n: return "N/A"
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "palworld"
    result = get_tiktok_hashtag(tag)
    print(json.dumps(result, indent=2, ensure_ascii=False))
