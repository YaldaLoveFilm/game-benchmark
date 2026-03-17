#!/usr/bin/env python3
"""TapTap benchmark — TapTap unofficial API (no key required)"""
import requests, json, sys

HEADERS = {
    "User-Agent": "TapTap/2.21.0-gplay (Android; 12)",
    "X-UA": "V=1&PN=TapTap&VN_CODE=2210200&VN=2.21.0&LANG=en_US&CH=default&UID=0",
    "Accept": "application/json",
}

def get_taptap_by_id(game_id):
    url = "https://www.taptap.io/webapiv2/app/v4/detail"
    params = {"id": game_id, "X-UA": "V=1&PN=TapTap&VN_CODE=2210200&VN=2.21.0&LANG=en_US"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        d = r.json().get("data", {})
        # Title is at top level, stat is also at top level
        title = d.get("title")
        stat = d.get("stat", {})
        rating = stat.get("rating", {})
        return {
            "platform": "TapTap",
            "name": title,
            "rating": rating.get("score"),
            "rating_count": stat.get("review_count"),
            "fans_count": stat.get("fans_count"),
            "hits_total": stat.get("hits_total"),
            "wishlist": stat.get("reserve_count"),
            "game_id": game_id,
            "url": f"https://www.taptap.io/app/{game_id}",
        }
    except Exception as e:
        return {"error": str(e)}

def search_taptap(keyword):
    url = "https://www.taptap.io/webapiv2/search/v1/result"
    params = {"q": keyword, "type": "app", "page_size": 1}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        hits = r.json().get("data", {}).get("hits", {}).get("list", [])
        if not hits:
            return {"error": f"No TapTap results for '{keyword}'"}
        app_id = hits[0].get("app", {}).get("id")
        if app_id:
            return get_taptap_by_id(app_id)
        return {"error": "Could not extract app ID"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "Palworld"
    if arg.isdigit():
        result = get_taptap_by_id(arg)
    else:
        result = search_taptap(arg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
