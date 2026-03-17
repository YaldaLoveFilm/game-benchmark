#!/usr/bin/env python3
"""App Store benchmark — iTunes Search API + Sensor Tower public estimates"""
import requests, json, sys, re

def get_sensortower_estimates(app_id):
    """Scrape public Sensor Tower page for download/revenue estimates (no login required)."""
    url = f"https://sensortower.com/ios/us/app/app/{app_id}/overview"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GameBenchmarkBot/1.0)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            # Try alternate URL format
            url2 = f"https://sensortower.com/overview/{app_id}?country=US"
            r = requests.get(url2, headers=headers, timeout=10)
        text = r.text
        downloads = None
        revenue = None
        # Parse "Last Month\n200K" or "Last Month $11M" patterns
        dl_match = re.search(r'Worldwide.*?Last Month\s*([\d.,]+[KMB]?)\s', text)
        rev_match = re.search(r'Revenue.*?Last Month\s*\$([\d.,]+[KMB]?)\s', text)
        if dl_match:
            downloads = dl_match.group(1)
        if rev_match:
            revenue = f"${rev_match.group(1)}"
        return {"downloads_last_month": downloads, "revenue_last_month": revenue}
    except:
        return {}

def search_appstore(query, country="us", limit=5):
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

        # Get Sensor Tower public estimates
        st = get_sensortower_estimates(app_id) if app_id else {}

        return {
            "platform": "App Store",
            "name": top.get("trackName"),
            "developer": top.get("artistName"),
            "rating": top.get("averageUserRating"),
            "rating_count": top.get("userRatingCount"),
            "rating_current_version": top.get("averageUserRatingForCurrentVersion"),
            "version": top.get("version"),
            "genres": top.get("genres", []),
            "price": top.get("formattedPrice", "Free"),
            "country": country.upper(),
            "url": top.get("trackViewUrl"),
            "app_id": app_id,
            # Sensor Tower public estimates
            "downloads_last_month_est": st.get("downloads_last_month"),
            "revenue_last_month_est": st.get("revenue_last_month"),
            "downloads_source": "Sensor Tower (public estimate)" if st.get("downloads_last_month") else None,
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Palworld"
    result = search_appstore(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
