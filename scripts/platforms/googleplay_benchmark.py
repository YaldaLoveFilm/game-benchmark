#!/usr/bin/env python3
"""Google Play benchmark — ratings + install counts + review opinions"""
import json, sys

def get_googleplay(bundle_id=None, query=None, country="us"):
    """
    Fetch Google Play data. Prefer bundle_id for accuracy; fallback to search query.
    """
    try:
        from google_play_scraper import app as gp_app, search as gp_search, reviews as gp_reviews, Sort
    except ImportError:
        return {"error": "google-play-scraper not installed"}

    try:
        if bundle_id:
            data = gp_app(bundle_id, lang="en", country=country)
        elif query:
            results = gp_search(query, lang="en", country=country, n_hits=3)
            if not results:
                return {"error": f"No Google Play results for '{query}'"}
            data = gp_app(results[0]["appId"], lang="en", country=country) if results[0].get("appId") else results[0]
        else:
            return {"error": "Need bundle_id or query"}

        if not data.get("title"):
            return {"error": "App not found on Google Play"}

        # Fetch reviews
        review_data, _ = gp_reviews(
            data.get("appId") or bundle_id,
            lang="en", country=country,
            sort=Sort.MOST_RELEVANT, count=20
        )
        pos = [r for r in review_data if r.get("score", 0) >= 4]
        neg = [r for r in review_data if r.get("score", 0) <= 2]

        def snippets(items, n=3):
            out = []
            seen = set()
            for r in items:
                text = (r.get("content") or "")[:120].strip()
                if text and text not in seen:
                    seen.add(text)
                    out.append(f"[{r['score']}★] {text}")
                if len(out) >= n: break
            return out

        return {
            "platform": "Google Play",
            "name": data.get("title"),
            "developer": data.get("developer"),
            "app_id": data.get("appId") or bundle_id,
            "rating": round(data.get("score", 0), 2),
            "rating_count": data.get("ratings"),
            "installs": data.get("installs"),
            "real_installs": data.get("realInstalls"),
            "price": data.get("price", 0),
            "free": data.get("free"),
            "genre": data.get("genre"),
            "content_rating": data.get("contentRating"),
            "last_updated": data.get("lastUpdatedOn"),
            "version": data.get("version"),
            "url": f"https://play.google.com/store/apps/details?id={data.get('appId') or bundle_id}",
            "review_summary": {
                "total_sampled": len(review_data),
                "positive_count": len(pos),
                "negative_count": len(neg),
                "positive_snippets": snippets(pos),
                "negative_snippets": snippets(neg),
            },
        }
    except Exception as e:
        return {"error": str(e)}

# Backward compat
def get_googleplay_stats(bundle_id, country="us"):
    return get_googleplay(bundle_id=bundle_id, country=country)

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Palworld"
    result = get_googleplay(query=q)
    print(json.dumps(result, indent=2, ensure_ascii=False))
