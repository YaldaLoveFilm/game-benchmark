#!/usr/bin/env python3
"""
Creator Ecosystem Analysis — YouTube Data API
Analyzes content creator landscape for a game:
1. Creator count estimate (how many channels cover this game)
2. Top creators by subscriber count (for partnership targeting)
"""
import os, requests, json, sys, argparse
from datetime import datetime, timedelta

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
BASE = "https://www.googleapis.com/youtube/v3"

def yt(endpoint, **params):
    params["key"] = YOUTUBE_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=10)
    if r.status_code != 200:
        return {}
    return r.json()

def fmt_num(n):
    if n is None: return "N/A"
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def get_channel_details(channel_ids):
    """Get subscriber counts and stats for a list of channel IDs."""
    if not channel_ids:
        return {}
    ids = ",".join(channel_ids[:50])
    data = yt("channels", part="snippet,statistics", id=ids)
    result = {}
    for item in data.get("items", []):
        cid = item["id"]
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        result[cid] = {
            "channel_id": cid,
            "channel_name": snippet.get("title", "Unknown"),
            "subscribers": int(stats.get("subscriberCount", 0)) if not stats.get("hiddenSubscriberCount") else None,
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "country": snippet.get("country", ""),
            "url": f"https://www.youtube.com/channel/{cid}",
        }
    return result

def search_creators(game_name, max_results=50):
    """
    Search for channels that create content about a game.
    Uses multiple search queries to get broader coverage.
    Returns deduplicated list of channel IDs.
    """
    channel_ids = set()
    queries = [
        game_name,
        f"{game_name} gameplay",
        f"{game_name} guide",
        f"{game_name} review",
        f"{game_name} tips",
    ]

    for query in queries:
        # Search for videos, extract unique channel IDs
        data = yt("search",
                  part="snippet",
                  q=query,
                  type="video",
                  order="viewCount",
                  maxResults=25,
                  publishedAfter=(datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for item in data.get("items", []):
            cid = item["snippet"].get("channelId")
            if cid:
                channel_ids.add(cid)
        if len(channel_ids) >= max_results:
            break

    return list(channel_ids)

def estimate_creator_count(game_name):
    """
    Estimate how many YouTube creators cover this game.
    Uses totalResults from search API (approximate, capped at ~500K by Google).
    """
    data = yt("search",
              part="id",
              q=game_name,
              type="video",
              maxResults=1)
    total = data.get("pageInfo", {}).get("totalResults", 0)
    return total

def get_top_creators(game_name, top_n=20):
    """
    Get top N creators by subscriber count for a game.
    """
    print(f"  Searching YouTube for '{game_name}' creators...")
    channel_ids = search_creators(game_name, max_results=50)
    print(f"  Found {len(channel_ids)} unique channels, fetching stats...")

    details = get_channel_details(channel_ids)

    # Sort by subscriber count (descending), put hidden/unknown at end
    sorted_channels = sorted(
        details.values(),
        key=lambda x: x["subscribers"] if x["subscribers"] is not None else -1,
        reverse=True
    )

    return sorted_channels[:top_n]

def analyze_creator_ecosystem(game_name, top_n=20, verbose=True):
    """Main entry point."""
    result = {
        "platform": "YouTube",
        "game": game_name,
        "video_count_estimate": None,
        "top_creators": [],
    }

    # 1. Creator count estimate
    total_videos = estimate_creator_count(game_name)
    result["video_count_estimate"] = total_videos

    # 2. Top creators
    top = get_top_creators(game_name, top_n)
    result["top_creators"] = top

    if verbose:
        print(f"\n{'─'*50}")
        print(f"  🎬 Creator Ecosystem  [{game_name}]")
        print(f"{'─'*50}")
        print(f"  YouTube total video results: ~{fmt_num(total_videos)}")
        print(f"  Creators analyzed: {len(top)}")
        print()

        # Group by tier
        mega   = [c for c in top if c["subscribers"] and c["subscribers"] >= 1_000_000]
        macro  = [c for c in top if c["subscribers"] and 100_000 <= c["subscribers"] < 1_000_000]
        mid    = [c for c in top if c["subscribers"] and 10_000 <= c["subscribers"] < 100_000]
        micro  = [c for c in top if c["subscribers"] and c["subscribers"] < 10_000]
        hidden = [c for c in top if c["subscribers"] is None]

        if mega:
            print(f"  🏆 Mega (1M+): {len(mega)} creators")
        if macro:
            print(f"  ⭐ Macro (100K-1M): {len(macro)} creators")
        if mid:
            print(f"  📈 Mid (10K-100K): {len(mid)} creators")
        if micro:
            print(f"  🌱 Micro (<10K): {len(micro)} creators")

        print()
        print(f"  Top {min(top_n, len(top))} creators by subscribers:")
        print(f"  {'#':<4} {'Channel':<35} {'Subscribers':<12} {'Total Views':<14} {'Country'}")
        print(f"  {'─'*4} {'─'*35} {'─'*12} {'─'*14} {'─'*8}")

        for i, c in enumerate(top[:top_n], 1):
            subs = fmt_num(c["subscribers"]) if c["subscribers"] else "Hidden"
            views = fmt_num(c["total_views"])
            country = c.get("country", "")
            name = c["channel_name"][:34]
            print(f"  {i:<4} {name:<35} {subs:<12} {views:<14} {country}")

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Creator Ecosystem Analysis")
    parser.add_argument("game", help="Game name")
    parser.add_argument("--top", type=int, default=20, help="Number of top creators to show")
    parser.add_argument("--output", help="Save JSON to file")
    args = parser.parse_args()

    result = analyze_creator_ecosystem(args.game, top_n=args.top)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Saved to {args.output}")
