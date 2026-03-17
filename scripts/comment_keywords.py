#!/usr/bin/env python3
"""
Comment Deep Analysis — YouTube + Reddit
Extracts: hot keywords, sentiment, inferred events/activities, player pain points
"""
import os, requests, json, sys, re, argparse
from collections import Counter
from datetime import datetime, timedelta, timezone

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"

# ─── STOPWORDS ─────────────────────────────────────────────────────
STOPWORDS = {
    "the", "this", "that", "with", "from", "have", "been", "will",
    "they", "what", "when", "just", "your", "about", "game", "games",
    "https", "like", "also", "more", "very", "good", "love", "great",
    "best", "make", "need", "want", "play", "playing", "player", "players",
    "update", "characters", "character", "even", "still", "their", "there",
    "would", "could", "should", "really", "think", "does", "dont", "cant",
    "much", "many", "some", "know", "time", "every", "after", "before",
    "actually", "please", "hope", "wish", "lmao", "haha", "lol", "omg",
    "yeah", "okay", "well", "then", "here", "come", "going", "being",
    "getting", "youre", "thats", "theyre", "were", "said", "than",
}

# ─── SENTIMENT SIGNALS ─────────────────────────────────────────────
POSITIVE_WORDS = {
    "amazing", "awesome", "excellent", "perfect", "love", "loved", "great",
    "fantastic", "wonderful", "beautiful", "nice", "cool", "fun", "enjoy",
    "enjoyed", "happy", "glad", "best", "incredible", "outstanding", "fire",
    "banger", "goat", "insane", "sick", "hype", "hyped", "excited", "cant wait",
    "underrated", "recommend", "recommended", "favorite", "favourite",
}
NEGATIVE_WORDS = {
    "bad", "worse", "worst", "terrible", "awful", "hate", "hated", "boring",
    "broken", "laggy", "lag", "crash", "crashes", "bug", "bugs", "glitch",
    "glitches", "disappointing", "disappointed", "waste", "trash", "garbage",
    "overpriced", "pay2win", "p2w", "greedy", "dead", "dying", "unplayable",
    "frustrating", "annoying", "toxic", "quit", "quitting", "uninstall",
    "refund", "scam", "false", "misleading", "copied", "clone",
}
EVENT_SIGNALS = {
    "event", "update", "patch", "season", "chapter", "anniversary", "collab",
    "collaboration", "limited", "banner", "summon", "gacha", "new character",
    "new hero", "new mode", "new map", "new skin", "release", "launched",
    "coming soon", "leaked", "leak", "version", "maintenance",
}
PAINPOINT_SIGNALS = {
    "crash", "crashes", "crashing", "lag", "laggy", "lagging", "stuck",
    "freeze", "freezing", "server", "servers", "connection", "disconnect",
    "pay2win", "p2w", "grinding", "grind", "grindy", "unfair", "unbalanced",
    "hard", "impossible", "wallet", "expensive", "cost", "price", "support",
    "customer service", "banned", "account", "lost", "stolen",
}

def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return text

def extract_keywords(texts, top_n=20):
    words = []
    for t in texts:
        words.extend([w for w in clean_text(t).split()
                      if len(w) >= 4 and w.isalpha() and w not in STOPWORDS])
    return Counter(words).most_common(top_n)

def analyze_sentiment(texts):
    """Simple rule-based sentiment classification."""
    pos = neg = neutral = 0
    pos_examples = []
    neg_examples = []
    for t in texts:
        tl = t.lower()
        p = sum(1 for w in POSITIVE_WORDS if w in tl)
        n = sum(1 for w in NEGATIVE_WORDS if w in tl)
        if p > n:
            pos += 1
            if len(pos_examples) < 3:
                pos_examples.append(t[:100])
        elif n > p:
            neg += 1
            if len(neg_examples) < 3:
                neg_examples.append(t[:100])
        else:
            neutral += 1
    total = max(pos + neg + neutral, 1)
    return {
        "positive": pos, "negative": neg, "neutral": neutral,
        "positive_pct": round(pos / total * 100),
        "negative_pct": round(neg / total * 100),
        "positive_examples": pos_examples,
        "negative_examples": neg_examples,
    }

def infer_events(video_titles, texts):
    """Extract likely recent events/activities from video titles + comments."""
    combined = " ".join(video_titles + texts).lower()
    found_signals = []
    for sig in EVENT_SIGNALS:
        if sig in combined:
            found_signals.append(sig)
    # Extract video title patterns that suggest events
    event_titles = []
    for title in video_titles:
        tl = title.lower()
        if any(sig in tl for sig in EVENT_SIGNALS):
            event_titles.append(title)
    return {
        "event_keywords_found": found_signals[:10],
        "event_video_titles": event_titles[:5],
    }

def extract_painpoints(texts):
    """Find common player pain points."""
    hits = Counter()
    examples = {}
    for t in texts:
        tl = t.lower()
        for sig in PAINPOINT_SIGNALS:
            if sig in tl:
                hits[sig] += 1
                if sig not in examples:
                    examples[sig] = t[:120]
    top = hits.most_common(5)
    return {
        "top_painpoints": [{"issue": k, "mentions": v, "example": examples.get(k, "")}
                           for k, v in top]
    }

# ─── YOUTUBE ───────────────────────────────────────────────────────

def get_latest_videos(channel_id, max_results=10):
    if not YOUTUBE_API_KEY:
        return []
    r = requests.get(f"{YOUTUBE_BASE}/search", params={
        "key": YOUTUBE_API_KEY, "channelId": channel_id,
        "part": "snippet", "type": "video", "order": "date",
        "maxResults": max_results
    }, timeout=10)
    items = r.json().get("items", [])
    return [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "published": item["snippet"]["publishedAt"],
        }
        for item in items if item.get("id", {}).get("videoId")
    ]

def get_video_comments(video_id, max_comments=100):
    if not YOUTUBE_API_KEY:
        return []
    comments = []
    params = {
        "key": YOUTUBE_API_KEY, "videoId": video_id,
        "part": "snippet", "maxResults": 100,
        "textFormat": "plainText", "order": "relevance"
    }
    try:
        r = requests.get(f"{YOUTUBE_BASE}/commentThreads", params=params, timeout=10)
        for item in r.json().get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top["textDisplay"],
                "likes": top["likeCount"],
            })
            if len(comments) >= max_comments:
                break
    except:
        pass
    return comments

def analyze_youtube_comments(channel_id, game_name, max_videos=10):
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY not set"}
    if not channel_id:
        return {"error": "No YouTube channel ID provided"}

    video_items = get_latest_videos(channel_id, max_videos)
    if not video_items:
        return {"error": f"No recent videos for channel {channel_id}"}

    all_comments = []
    video_titles = [v["title"] for v in video_items]
    video_details = []

    for v in video_items:
        comments = get_video_comments(v["video_id"], 100)
        all_comments.extend([c["text"] for c in comments])
        top_liked = sorted(comments, key=lambda x: x["likes"], reverse=True)[:2]
        video_details.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "published": v["published"],
            "url": f"https://youtube.com/watch?v={v['video_id']}",
            "comment_count": len(comments),
            "top_liked_comments": [c["text"][:120] for c in top_liked],
        })

    keywords = extract_keywords(all_comments, top_n=20)
    sentiment = analyze_sentiment(all_comments)
    events = infer_events(video_titles, all_comments)
    painpoints = extract_painpoints(all_comments)

    return {
        "source": "YouTube Comments",
        "game": game_name,
        "videos_analyzed": len(video_items),
        "total_comments": len(all_comments),
        "recent_video_titles": video_titles[:5],
        "top_keywords": [{"word": w, "count": c} for w, c in keywords],
        "top_keywords_flat": [w for w, _ in keywords],
        "sentiment": sentiment,
        "inferred_events": events,
        "painpoints": painpoints,
        "video_details": video_details,
    }

# ─── REDDIT ────────────────────────────────────────────────────────

def get_reddit_comments(subreddit, sort="hot", limit=200):
    headers = {"User-Agent": "Mozilla/5.0 GameBenchmarkBot/1.0"}
    r = requests.get(f"https://www.reddit.com/r/{subreddit}/{sort}.json",
                     headers=headers, params={"limit": 25}, timeout=10)
    if r.status_code != 200:
        return [], []
    posts = r.json().get("data", {}).get("children", [])
    titles = [p["data"]["title"] for p in posts]
    texts = [p["data"]["title"] + " " + p["data"].get("selftext", "")
             for p in posts]
    if posts:
        top_post_id = posts[0]["data"]["id"]
        cr = requests.get(
            f"https://www.reddit.com/r/{subreddit}/comments/{top_post_id}.json",
            headers=headers, params={"limit": 100}, timeout=10
        )
        if cr.status_code == 200 and len(cr.json()) > 1:
            comment_data = cr.json()[1].get("data", {}).get("children", [])
            texts.extend([c["data"].get("body", "") for c in comment_data
                          if c["data"].get("body")])
    return texts, titles

def analyze_reddit_comments(subreddit, game_name):
    texts, titles = get_reddit_comments(subreddit)
    if not texts:
        return {"error": f"Could not fetch Reddit data for r/{subreddit}"}
    keywords = extract_keywords(texts, top_n=20)
    sentiment = analyze_sentiment(texts)
    events = infer_events(titles, texts)
    painpoints = extract_painpoints(texts)
    return {
        "source": "Reddit",
        "game": game_name,
        "subreddit": f"r/{subreddit}",
        "texts_analyzed": len(texts),
        "top_keywords": [{"word": w, "count": c} for w, c in keywords],
        "top_keywords_flat": [w for w, _ in keywords],
        "sentiment": sentiment,
        "inferred_events": events,
        "painpoints": painpoints,
    }

# ─── MAIN ──────────────────────────────────────────────────────────

def print_deep_analysis(label, result):
    if "error" in result:
        print(f"  ⚠️  {result['error']}")
        return

    print(f"\n  📊 {label}")
    print(f"  Analyzed: {result.get('videos_analyzed') or result.get('texts_analyzed')} sources "
          f"| {result.get('total_comments') or result.get('texts_analyzed')} texts")

    # Recent activity
    titles = result.get("recent_video_titles", [])
    if titles:
        print(f"\n  📹 Recent videos:")
        for t in titles[:5]:
            print(f"     • {t}")

    # Hot keywords
    kw = result.get("top_keywords_flat", [])
    if kw:
        print(f"\n  🔥 Hot keywords: {', '.join(kw[:12])}")

    # Sentiment
    s = result.get("sentiment", {})
    if s:
        bar_pos = "█" * (s["positive_pct"] // 5)
        bar_neg = "█" * (s["negative_pct"] // 5)
        neu_pct = 100 - s["positive_pct"] - s["negative_pct"]
        print(f"\n  😊 Sentiment: +{s['positive_pct']}% {bar_pos}  "
              f"-{s['negative_pct']}% {bar_neg}  ~{neu_pct}% neutral")
        if s.get("positive_examples"):
            print(f"     ✅ \"{s['positive_examples'][0][:80]}\"")
        if s.get("negative_examples"):
            print(f"     ❌ \"{s['negative_examples'][0][:80]}\"")

    # Inferred events
    ev = result.get("inferred_events", {})
    ev_titles = ev.get("event_video_titles", [])
    if ev_titles:
        print(f"\n  🎉 Inferred recent events/activities:")
        for t in ev_titles[:3]:
            print(f"     • {t}")
    elif ev.get("event_keywords_found"):
        print(f"\n  🎉 Event signals: {', '.join(ev['event_keywords_found'][:6])}")

    # Pain points
    pp = result.get("painpoints", {}).get("top_painpoints", [])
    if pp:
        print(f"\n  🔧 Player pain points:")
        for p in pp[:4]:
            print(f"     • [{p['mentions']}x] {p['issue']} — \"{p['example'][:80]}\"")


def run(args):
    results = {}
    print(f"\n{'═'*50}")
    print(f"  💬 DEEP COMMENT ANALYSIS: {args.game.upper()}")
    print(f"{'═'*50}")

    if args.youtube_channel:
        yt = analyze_youtube_comments(args.youtube_channel, args.game,
                                       max_videos=args.max_videos)
        results["youtube"] = yt
        print_deep_analysis("YouTube Comments", yt)

    if args.reddit:
        rd = analyze_reddit_comments(args.reddit, args.game)
        results["reddit"] = rd
        print_deep_analysis("Reddit", rd)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {args.output}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True)
    parser.add_argument("--youtube-channel", help="YouTube channel ID")
    parser.add_argument("--reddit", help="Subreddit name (without r/)")
    parser.add_argument("--max-videos", type=int, default=10)
    parser.add_argument("--output", help="Save results to JSON file")
    args = parser.parse_args()
    run(args)
