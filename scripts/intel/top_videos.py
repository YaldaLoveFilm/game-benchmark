#!/usr/bin/env python3
"""
Top Videos — Recent high-performing YouTube videos for a game.
Returns top N videos by view count with links, titles, publish date.
"""
import os, requests
from datetime import datetime, timedelta, timezone

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
BASE = "https://www.googleapis.com/youtube/v3"

def fmt_num(n):
    if n is None: return "N/A"
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def get_top_videos(game_name, days=90, top_n=5):
    """
    Fetch top N videos by view count for a game, published in last `days` days.
    Returns list of dicts with title, views, url, published_at, channel.
    """
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY not set"}

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Search for recent videos
    r = requests.get(f"{BASE}/search", params={
        "key": YOUTUBE_API_KEY,
        "q": game_name,
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "maxResults": 25,
        "publishedAfter": since,
    }, timeout=10)
    items = r.json().get("items", [])
    if not items:
        return {"error": f"No videos found for '{game_name}'"}

    video_ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]

    # Get exact view counts
    stats_r = requests.get(f"{BASE}/videos", params={
        "key": YOUTUBE_API_KEY,
        "id": ",".join(video_ids),
        "part": "snippet,statistics",
    }, timeout=10)

    videos = []
    for item in stats_r.json().get("items", []):
        vid = item["id"]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        videos.append({
            "video_id": vid,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", "")[:10],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "url": f"https://youtube.com/watch?v={vid}",
        })

    videos.sort(key=lambda x: x["views"], reverse=True)
    return {
        "game": game_name,
        "period_days": days,
        "videos": videos[:top_n],
    }

def print_top_videos(result):
    if "error" in result:
        print(f"  ⚠️  {result['error']}")
        return
    videos = result.get("videos", [])
    print(f"  Top {len(videos)} videos (last {result['period_days']} days):")
    print()
    for i, v in enumerate(videos, 1):
        print(f"  {i}. {v['title'][:65]}")
        print(f"     👁 {fmt_num(v['views'])} views · 👍 {fmt_num(v['likes'])} · 📅 {v['published_at']}")
        print(f"     🔗 {v['url']}")
        print(f"     📺 {v['channel']}")
        print()
