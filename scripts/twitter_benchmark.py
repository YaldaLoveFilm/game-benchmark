#!/usr/bin/env python3
"""X/Twitter benchmark — Nitter public instances (no key required, fallback to search)"""
import requests, json, sys, re
from collections import Counter

NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.net",
    "https://nitter.1d4.us",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GameBenchmark/2.0)"}

def search_nitter(query, instance=None):
    """Scrape Nitter search for tweet mentions"""
    instances = [instance] if instance else NITTER_INSTANCES
    for base in instances:
        try:
            url = f"{base}/search"
            params = {"q": query, "f": "tweets"}
            r = requests.get(url, params=params, headers=HEADERS, timeout=8)
            if r.status_code == 200 and "tweet" in r.text.lower():
                # Extract tweet texts
                tweets = re.findall(r'class="tweet-content[^"]*"[^>]*>(.*?)</div>', r.text, re.DOTALL)
                clean_tweets = [re.sub(r'<[^>]+>', '', t).strip() for t in tweets[:50]]

                # Word frequency for sentiment proxy
                words = []
                for t in clean_tweets:
                    words.extend([w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', t)])
                stopwords = {"this", "that", "with", "from", "have", "been", "will", "they", "what", "when", "just", "your", "about", "game", "https", "twitter"}
                freq = Counter(w for w in words if w not in stopwords).most_common(12)

                # Count mentions
                mention_count = len(re.findall(r'class="tweet-content', r.text))

                return {
                    "platform": "X / Twitter",
                    "query": query,
                    "mentions_on_page": mention_count,
                    "top_keywords": [w for w, _ in freq],
                    "sample_tweets": clean_tweets[:5],
                    "source": f"Nitter ({base})",
                    "note": "Page-level count only; full volume requires Twitter API v2",
                }
        except:
            continue

    return {
        "platform": "X / Twitter",
        "query": query,
        "error": "All Nitter instances failed or unavailable. For accurate data, configure TWITTER_BEARER_TOKEN.",
        "note": "Alternatively use: https://x.com/search?q=" + query.replace(" ", "+"),
    }

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Palworld"
    result = search_nitter(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
