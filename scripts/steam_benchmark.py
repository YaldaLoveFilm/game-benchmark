#!/usr/bin/env python3
import os
import requests
import json
import sys

def get_current_players(appid):
    api_key = os.environ.get('STEAM_API_KEY')
    if not api_key:
        return {"error": "STEAM_API_KEY not found in environment"}
    
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('response', {}).get('result') == 1:
            return {"appid": appid, "player_count": data['response']['player_count']}
        else:
            return {"error": f"Failed to get player count for AppID {appid}"}
    except Exception as e:
        return {"error": str(e)}

def get_game_info(appid):
    # Store API - no key required usually
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get(str(appid), {}).get('success'):
            info = data[str(appid)]['data']
            return {
                "name": info.get('name'),
                "description": info.get('short_description'),
                "release_date": info.get('release_date', {}).get('date'),
                "genres": [g['description'] for g in info.get('genres', [])]
            }
        else:
            return {"error": f"Failed to get game info for AppID {appid}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No AppID provided"}))
        sys.exit(1)
    
    appid = sys.argv[1]
    players = get_current_players(appid)
    info = get_game_info(appid)
    
    result = {**info, **players}
    print(json.dumps(result, indent=2))
