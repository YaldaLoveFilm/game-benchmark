#!/usr/bin/env python3
"""Google Play benchmark — google-play-scraper (no key required)"""
import json, sys

def get_googleplay(app_id, lang="en", country="us"):
    try:
        from google_play_scraper import app, search
        # Try direct app ID lookup first
        if "." in app_id:
            data = app(app_id, lang=lang, country=country)
        else:
            # Search by keyword
            results = search(app_id, n_hits=1, lang=lang, country=country)
            if not results:
                return {"error": f"No Google Play results for '{app_id}'"}
            data = app(results[0]["appId"], lang=lang, country=country)

        return {
            "platform": "Google Play",
            "name": data.get("title"),
            "developer": data.get("developer"),
            "rating": round(data.get("score", 0), 2),
            "rating_count": data.get("ratings"),
            "reviews": data.get("reviews"),
            "installs": f"{data.get('realInstalls'):,}" if data.get("realInstalls") else data.get("installs"),
            "real_installs": data.get("realInstalls"),
            "price": data.get("price", 0),
            "free": data.get("free"),
            "genre": data.get("genre"),
            "content_rating": data.get("contentRating"),
            "last_updated": data.get("updated"),
            "version": data.get("version"),
            "app_id": data.get("appId"),
            "url": data.get("url"),
        }
    except ImportError:
        return {"error": "google-play-scraper not installed. Run: pip install google-play-scraper"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app_id = sys.argv[1] if len(sys.argv) > 1 else "com.pocketpair.palworld"
    result = get_googleplay(app_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
