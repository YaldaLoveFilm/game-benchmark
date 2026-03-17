#!/usr/bin/env python3
"""Twitch benchmark — Twitch Helix API (requires TWITCH_CLIENT_ID + TWITCH_CLIENT_SECRET)"""
import os, requests, json, sys

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET", "")

def get_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    try:
        r = requests.post("https://id.twitch.tv/oauth2/token", params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }, timeout=10)
        return r.json().get("access_token")
    except:
        return None

def get_twitch_stats(game_name):
    if not CLIENT_ID or not CLIENT_SECRET:
        return {"error": "TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET not set. Register free at dev.twitch.tv"}
    token = get_token()
    if not token:
        return {"error": "Failed to obtain Twitch OAuth token"}
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    try:
        # Get Game ID
        gr = requests.get("https://api.twitch.tv/helix/games",
                          headers=headers, params={"name": game_name}, timeout=10)
        game_data = gr.json().get("data", [])
        if not game_data:
            return {"error": f"Game '{game_name}' not found on Twitch"}
        game_id = game_data[0]["id"]
        box_art = game_data[0].get("box_art_url", "").replace("{width}x{height}", "138x190")

        # Get live streams (top 100)
        sr = requests.get("https://api.twitch.tv/helix/streams",
                          headers=headers, params={"game_id": game_id, "first": 100}, timeout=10)
        streams = sr.json().get("data", [])
        total_viewers = sum(s["viewer_count"] for s in streams)
        top_streams = sorted(streams, key=lambda x: x["viewer_count"], reverse=True)[:3]

        # Get channel/game followers via IGDB (fallback: just report stream count)
        return {
            "platform": "Twitch",
            "game": game_name,
            "game_id": game_id,
            "live_streams": len(streams),
            "total_viewers": total_viewers,
            "top_streamers": [
                {
                    "channel": s["user_name"],
                    "viewers": s["viewer_count"],
                    "title": s["title"][:60],
                    "url": f"https://twitch.tv/{s['user_login']}",
                    "language": s.get("language", "?"),
                }
                for s in top_streams
            ],
            "box_art": box_art,
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    game = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Wuthering Waves"
    result = get_twitch_stats(game)
    print(json.dumps(result, indent=2, ensure_ascii=False))
