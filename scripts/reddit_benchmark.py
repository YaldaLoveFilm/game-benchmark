#!/usr/bin/env python3
"""Reddit benchmark — PRAW or public JSON API (optional REDDIT_CLIENT_ID/SECRET)"""
import os, requests, json, sys
from collections import Counter

HEADERS = {"User-Agent": "GameBenchmark/2.0 (by /u/game_benchmark_bot)"}
BASE = "https://www.reddit.com"

def get_subreddit_stats(subreddit):
    """Get subreddit info and recent post activity via public JSON API"""
    try:
        # Subreddit info
        r = requests.get(f"{BASE}/r/{subreddit}/about.json", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", {})
        subscribers = data.get("subscribers", 0)
        active_users = data.get("accounts_active", 0)
        title = data.get("title", subreddit)

        # Recent top posts (7 days)
        r2 = requests.get(f"{BASE}/r/{subreddit}/top.json",
                          headers=HEADERS, params={"t": "week", "limit": 25}, timeout=10)
        r2.raise_for_status()
        posts = r2.json().get("data", {}).get("children", [])

        total_upvotes = sum(p["data"].get("score", 0) for p in posts)
        total_comments = sum(p["data"].get("num_comments", 0) for p in posts)

        # Simple sentiment: top recurring words in post titles
        words = []
        for p in posts:
            title_text = p["data"].get("title", "").lower()
            words.extend([w for w in title_text.split() if len(w) > 4 and w.isalpha()])
        stopwords = {"this", "that", "with", "from", "have", "been", "will", "they", "what", "when", "just", "your", "about", "game", "after"}
        word_freq = Counter(w for w in words if w not in stopwords).most_common(10)

        top_posts = [
            {
                "title": p["data"]["title"][:70],
                "score": p["data"]["score"],
                "comments": p["data"]["num_comments"],
                "url": f"https://reddit.com{p['data']['permalink']}",
            }
            for p in sorted(posts, key=lambda x: x["data"]["score"], reverse=True)[:3]
        ]

        return {
            "platform": "Reddit",
            "subreddit": f"r/{subreddit}",
            "title": title,
            "subscribers": subscribers,
            "active_users_now": active_users,
            "top_posts_7d": len(posts),
            "total_upvotes_7d": total_upvotes,
            "total_comments_7d": total_comments,
            "avg_upvotes_per_post": total_upvotes // len(posts) if posts else 0,
            "top_keywords_7d": [w for w, _ in word_freq],
            "top_3_posts": top_posts,
            "url": f"https://reddit.com/r/{subreddit}",
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Subreddit r/{subreddit} not found"}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    subreddit = sys.argv[1] if len(sys.argv) > 1 else "Palworld"
    result = get_subreddit_stats(subreddit)
    print(json.dumps(result, indent=2, ensure_ascii=False))
