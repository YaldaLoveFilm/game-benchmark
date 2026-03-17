#!/usr/bin/env python3
"""
Quick Benchmark — 只需游戏名，自动完成全平台调研
Usage: python3 quick_benchmark.py "游戏名"
"""
import os, sys, json, subprocess, argparse
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "games_db.json"
SCRIPTS = Path(__file__).parent

def load_db():
    if DB_PATH.exists():
        d = json.loads(DB_PATH.read_text())
        return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}

def run(game_name, output_json=None):
    db = load_db()
    game_data = db.get(game_name)

    env = os.environ.copy()
    env["YOUTUBE_API_KEY"] = env.get("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
    env["STEAM_API_KEY"]   = env.get("STEAM_API_KEY", "YOUR_STEAM_API_KEY")

    # Build CLI args
    cmd = [
        sys.executable, str(SCRIPTS / "benchmark_all.py"),
        "--game", game_name,
        "--auto-discover",
        "--save-discovery",
    ]

    if game_data:
        if game_data.get("steam_id"):
            cmd += ["--steam-id", game_data["steam_id"]]
        if game_data.get("google_play_bundle"):
            cmd += ["--bundle", game_data["google_play_bundle"]]
        if game_data.get("taptap_id"):
            cmd += ["--taptap-id", game_data["taptap_id"]]
        if game_data.get("reddit"):
            cmd += ["--reddit", game_data["reddit"]]
        if game_data.get("tiktok_hashtag"):
            cmd += ["--tiktok", game_data["tiktok_hashtag"]]
        if game_data.get("youtube_query"):
            cmd += ["--youtube", game_data["youtube_query"]]
        ch = game_data.get("official_accounts", {}).get("youtube_channel_id")
        if ch:
            cmd += ["--comment-channel", ch, "--comment-reddit", game_data.get("reddit", "")]
        cmd += ["--db-game", game_name]

    if output_json:
        cmd += ["--output", str(output_json)]

    cmd = [c for c in cmd if c is not None]  # remove any None args
    result = subprocess.run(cmd, env=env, capture_output=False)
    return result.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("game", help="游戏名称，例如：Wuthering Waves")
    parser.add_argument("--output", help="保存 JSON 数据到文件")
    args = parser.parse_args()
    sys.exit(run(args.game, args.output))
