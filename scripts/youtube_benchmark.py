#!/usr/bin/env python3
"""YouTube benchmark — YouTube Data API v3 (requires YOUTUBE_API_KEY)"""
import os, requests, json, sys
from datetime import datetime, timedelta, timezone

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
BASE = "https://www.googleapis.com/youtube/v3"

def search_videos(query, days=7, max_results=50):
    if not API_KEY:
        return {"error": "YOUTUBE_API_KEY not set"}
    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{BASE}/search"
    params = {
        "key": API_KEY,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "publishedAfter": published_after,
        "order": "viewCount",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        total_results = data.get("pageInfo", {}).get("totalResults", 0)
        video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        return video_ids, total_results
    except Exception as e:
        return [], 0

def get_video_stats(video_ids):
    if not video_ids or not API_KEY:
        return []
    url = f"{BASE}/videos"
    params = {"key": API_KEY, "id": ",".join(video_ids), "part": "statistics,snippet"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])
    except:
        return []

def benchmark_youtube(query, days=7):
    video_ids, total_results = search_videos(query, days=days)
    if not video_ids:
        return {"error": f"No YouTube videos found for '{query}'"}
    stats = get_video_stats(video_ids)
    total_views = sum(int(v.get("statistics", {}).get("viewCount", 0)) for v in stats)
    total_likes = sum(int(v.get("statistics", {}).get("likeCount", 0)) for v in stats)
    top_videos = sorted(stats, key=lambda v: int(v.get("statistics", {}).get("viewCount", 0)), reverse=True)[:3]
    top_list = [
        {
            "title": v["snippet"]["title"][:60],
            "channel": v["snippet"]["channelTitle"],
            "views": int(v["statistics"].get("viewCount", 0)),
            "url": f"https://youtube.com/watch?v={v['id']}",
        }
        for v in top_videos
    ]
    return {
        "platform": "YouTube",
        "query": query,
        "period_days": days,
        "videos_found_in_period": total_results,
        "sample_size": len(stats),
        "total_views_sample": total_views,
        "total_likes_sample": total_likes,
        "avg_views_per_video": total_views // len(stats) if stats else 0,
        "top_videos": top_list,
    }

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Palworld"
    result = benchmark_youtube(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
