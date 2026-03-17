#!/usr/bin/env python3
"""App Store benchmark — ratings + review opinions (iTunes APIs, no key required)"""
import requests, json, sys, re

def get_appstore_reviews(app_id, country="us", limit=50):
    """Fetch recent reviews via iTunes RSS."""
    try:
        r = requests.get(
            f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortby=mostrecent/json",
            timeout=10
        )
        entries = r.json().get("feed", {}).get("entry", [])
        reviews = []
        for e in entries[1:]:  # skip first entry (app info)
            rating = int(e.get("im:rating", {}).get("label", 0))
            title  = e.get("title", {}).get("label", "")
            body   = e.get("content", {}).get("label", "")
            reviews.append({"rating": rating, "title": title, "body": body})
            if len(reviews) >= limit:
                break
        return reviews
    except Exception:
        return []

def summarize_reviews(reviews):
    """Extract opinion themes from reviews."""
    if not reviews:
        return {}

    pos = [r for r in reviews if r["rating"] >= 4]
    neg = [r for r in reviews if r["rating"] <= 2]

    def top_snippets(items, n=3):
        seen = set()
        out = []
        for r in items:
            text = (r["body"] or r["title"])[:120].strip()
            if text and text not in seen:
                seen.add(text)
                out.append(f"[{r['rating']}★] {text}")
            if len(out) >= n:
                break
        return out

    avg = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else 0
    return {
        "total_sampled": len(reviews),
        "avg_rating_sample": avg,
        "positive_count": len(pos),
        "negative_count": len(neg),
        "positive_snippets": top_snippets(pos),
        "negative_snippets": top_snippets(neg),
    }

def get_appstore(query, country="us", limit=5):
    url = "https://itunes.apple.com/search"
    params = {"term": query, "country": country, "media": "software", "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return {"error": f"No App Store results for '{query}'"}
        top = results[0]
        app_id = top.get("trackId")

        reviews = get_appstore_reviews(app_id, country) if app_id else []
        review_summary = summarize_reviews(reviews)

        return {
            "platform": "App Store",
            "name": top.get("trackName"),
            "developer": top.get("artistName"),
            "app_id": app_id,
            "rating": top.get("averageUserRating"),
            "rating_count": top.get("userRatingCount"),
            "rating_current_version": top.get("averageUserRatingForCurrentVersion"),
            "version": top.get("version"),
            "genres": top.get("genres", []),
            "price": top.get("formattedPrice", "Free"),
            "country": country.upper(),
            "url": top.get("trackViewUrl"),
            "review_summary": review_summary,
        }
    except Exception as e:
        return {"error": str(e)}

# Keep old name for backward compat
search_appstore = get_appstore

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Palworld"
    result = get_appstore(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
