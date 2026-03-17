#!/usr/bin/env python3
"""
Game Benchmark — Full Platform Research (v3 dispatcher)
Each data dimension is handled by a dedicated module in platforms/, social/, intel/.

Usage:
  python3 benchmark_all.py --game "Wuthering Waves" --bundle com.kurogame.wutheringwaves.global
  python3 benchmark_all.py --game "Palmon" --auto-discover
"""
import argparse, json, sys, os, requests
from pathlib import Path

# ── API Keys ──────────────────────────────────────────────────────
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
STEAM_API_KEY   = os.environ.get("STEAM_API_KEY",   "")
TAVILY_API_KEY  = os.environ.get("TAVILY_API_KEY",  "")

# ── Script dir on sys.path ────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / "platforms"))
sys.path.insert(0, str(SCRIPTS_DIR / "social"))
sys.path.insert(0, str(SCRIPTS_DIR / "intel"))

# ── Platform modules ──────────────────────────────────────────────
from steam_benchmark       import get_current_players, get_game_info
from taptap_benchmark      import get_taptap_by_id as get_taptap_stats
from youtube_benchmark     import benchmark_youtube
from tiktok_benchmark      import get_tiktok_hashtag as get_tiktok_stats
from reddit_benchmark      import get_subreddit_stats as get_reddit_stats
from twitter_benchmark     import search_nitter as get_twitter_stats
from twitch_benchmark      import get_twitch_stats
from discover_accounts     import discover_game

# ── New modular imports ───────────────────────────────────────────
from platforms.appstore_benchmark    import get_appstore
from platforms.googleplay_benchmark  import get_googleplay
from social.social_accounts          import get_all_social_accounts, print_social_accounts
from intel.top_videos                import get_top_videos, print_top_videos
from intel.regional_distribution     import analyze_regional_distribution, print_regional_distribution
from intel.top_videos                import fmt_num as fmt_num_vids
from creator_ecosystem               import analyze_creator_ecosystem
from comment_keywords                import analyze_youtube_comments, analyze_reddit_comments, print_deep_analysis
from intel.html_report               import save_report
from intel.publish                   import publish_report

# ── Helpers ───────────────────────────────────────────────────────
def fmt_num(n):
    if n is None: return "N/A"
    try: n = int(n)
    except: return str(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)

def print_section(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")

def print_kv(k, v):
    if v is not None and v != "" and v != "N/A":
        print(f"  {k:<22} {v}")

def print_review_summary(summary, platform=""):
    if not summary: return
    pos = summary.get("positive_snippets", [])
    neg = summary.get("negative_snippets", [])
    n_pos = summary.get("positive_count", 0)
    n_neg = summary.get("negative_count", 0)
    total = summary.get("total_sampled", 0)
    if not total: return
    print(f"  Reviews sampled: {total}  ·  👍 {n_pos} positive  ·  👎 {n_neg} negative")
    if pos:
        print(f"  Positive opinions:")
        for s in pos[:2]:
            print(f"    ✅ {s[:110]}")
    if neg:
        print(f"  Negative opinions:")
        for s in neg[:3]:
            print(f"    ❌ {s[:110]}")


# ── Main benchmark ────────────────────────────────────────────────
def run_benchmark(args):
    game = args.game
    results = {}

    # ── Load games_db early ────────────────────────────────────────
    game_db_data = None
    db_path = Path(__file__).parent.parent / "games_db.json"
    lookup_name = getattr(args, "db_game", None) or game
    if db_path.exists():
        import json as _json
        _db = _json.loads(db_path.read_text())
        game_db_data = _db.get(lookup_name)

    print(f"\n{'═'*50}")
    print(f"  🎮 GAME BENCHMARK: {game.upper()}")
    print(f"{'═'*50}")

    # ── Steam ──────────────────────────────────────────────────────
    if args.steam_id:
        print_section("📊 Steam")
        players = get_current_players(args.steam_id)
        info    = get_game_info(args.steam_id)
        steam   = {**info, **players}
        results["steam"] = steam
        if "error" not in steam:
            print_kv("Game Name",       steam.get("name"))
            print_kv("Current Players", fmt_num(steam.get("player_count")))
            print_kv("Genres",          ", ".join(steam.get("genres", [])))
            print_kv("Release Date",    steam.get("release_date"))
        else:
            print(f"  ⚠️  {steam['error']}")

    # ── App Store ──────────────────────────────────────────────────
    print_section("🍎 App Store")
    appstore = get_appstore(game)
    results["appstore"] = appstore
    if "error" not in appstore:
        print_kv("Name",    appstore.get("name"))
        print_kv("Rating",  f"{appstore.get('rating', 'N/A')} / 5.0  ({fmt_num(appstore.get('rating_count'))} reviews)")
        # Sensor Tower cache
        if game_db_data and game_db_data.get("sensortower", {}).get("downloads_last_month"):
            st = game_db_data["sensortower"]
            print_kv("Downloads (last mo.)",  f"~{st['downloads_last_month']}  [Sensor Tower {st.get('as_of','')}]")
            if st.get("revenue_last_month"):
                print_kv("Revenue (last mo.)", f"{st['revenue_last_month']}  [Sensor Tower]")
        print_kv("Price",   appstore.get("price"))
        print_kv("Version", appstore.get("version"))
        print()
        print_review_summary(appstore.get("review_summary"), "App Store")
    else:
        print(f"  ⚠️  {appstore['error']}")

    # ── Google Play ────────────────────────────────────────────────
    print_section("🤖 Google Play")
    bundle = getattr(args, "bundle", None) or (game_db_data or {}).get("google_play_bundle")
    gplay = get_googleplay(bundle_id=bundle, query=game if not bundle else None)
    results["googleplay"] = gplay
    if "error" not in gplay:
        print_kv("Name",      gplay.get("name"))
        print_kv("Developer", gplay.get("developer"))
        print_kv("Rating",    f"{gplay.get('rating', 'N/A')} / 5.0  ({fmt_num(gplay.get('rating_count'))} ratings)")
        ri = gplay.get("real_installs")
        print_kv("Installs",  f"{ri:,}" if ri else gplay.get("installs"))
        print_kv("Version",   gplay.get("version"))
        print()
        print_review_summary(gplay.get("review_summary"), "Google Play")
    else:
        print(f"  ⚠️  {gplay['error']}")

    # ── TapTap ────────────────────────────────────────────────────
    taptap_id = getattr(args, "taptap_id", None) or (game_db_data or {}).get("taptap_id")
    if taptap_id:
        print_section("🟢 TapTap")
        taptap = get_taptap_stats(taptap_id)
        results["taptap"] = taptap
        if "error" not in taptap:
            print_kv("Name",      taptap.get("name"))
            print_kv("Rating",    f"{taptap.get('rating', 'N/A')}  ({fmt_num(taptap.get('rating_count'))} ratings)")
            print_kv("Hits",      fmt_num(taptap.get("hits_total")))
        else:
            print(f"  ⚠️  {taptap['error']}")

    # ── YouTube (trending videos) ──────────────────────────────────
    yt_query = getattr(args, "youtube", None) or f"{game} gameplay"
    print_section(f"▶️  YouTube  [{yt_query}]")
    yt = benchmark_youtube(yt_query)
    results["youtube"] = yt
    if "error" not in yt:
        print_kv("Videos (7d)",      fmt_num(yt.get("video_count")))
        print_kv("Total Views",      fmt_num(yt.get("total_views")))
        print_kv("Avg Views/Video",  fmt_num(yt.get("avg_views")))

    # ── Top Videos ────────────────────────────────────────────────
    print_section(f"🏆 Top Videos (90 days)")
    top_vids = get_top_videos(game, days=90, top_n=5)
    results["top_videos"] = top_vids
    print_top_videos(top_vids)

    # ── TikTok ────────────────────────────────────────────────────
    tt_tag = getattr(args, "tiktok", None) or game.lower().replace(" ", "")
    print_section(f"🎵 TikTok  [#{tt_tag}]")
    tt = get_tiktok_stats(tt_tag)
    results["tiktok"] = tt
    if "error" not in tt:
        print_kv("Views", fmt_num(tt.get("views")))
    else:
        print(f"  ⚠️  {tt['error']}")

    # ── Reddit ────────────────────────────────────────────────────
    reddit_sub = getattr(args, "reddit", None) or (game_db_data or {}).get("reddit") or game.replace(" ", "")
    print_section(f"🔴 Reddit  [r/{reddit_sub}]")
    rd = get_reddit_stats(reddit_sub)
    results["reddit"] = rd
    if "error" not in rd:
        print_kv("Subscribers", fmt_num(rd.get("subscribers")))
        print_kv("Active Users", fmt_num(rd.get("active_users")))
    else:
        print(f"  ⚠️  {rd['error']}")

    # ── Twitter / X ───────────────────────────────────────────────
    tw_query = getattr(args, "twitter", None) or game
    print_section(f"🐦 X / Twitter  [{tw_query}]")
    tw = get_twitter_stats(tw_query)
    results["twitter"] = tw
    if "error" not in tw:
        print_kv("Recent Tweets", fmt_num(tw.get("tweet_count")))
    else:
        print(f"  ⚠️  {tw['error']}")

    # ── Twitch ────────────────────────────────────────────────────
    twitch_q = getattr(args, "twitch", None) or game
    print_section(f"🟣 Twitch  [{twitch_q}]")
    twitch = get_twitch_stats(twitch_q)
    results["twitch"] = twitch
    if "error" not in twitch:
        print_kv("Viewers Now", fmt_num(twitch.get("viewer_count")))
    else:
        print(f"  ⚠️  {twitch['error']}")

    # ── Auto-discover / load official accounts from DB ─────────────
    if not game_db_data and getattr(args, "auto_discover", False):
        print_section(f"🔍 Auto-discovering: {lookup_name}")
        game_db_data = discover_game(
            lookup_name,
            save_to_db=getattr(args, "save_discovery", False),
            verbose=False
        )
        if game_db_data:
            print(f"  ✅ Discovery complete")
            if not bundle and game_db_data.get("google_play_bundle"):
                args.bundle = game_db_data["google_play_bundle"]
            if not taptap_id and game_db_data.get("taptap_id"):
                args.taptap_id = game_db_data["taptap_id"]
            if getattr(args, "save_discovery", False):
                print(f"  💾 Saved to games_db.json")

    # ── Official Social Accounts ───────────────────────────────────
    print_section(f"🏢 Official Accounts  [{lookup_name}]")
    db_accounts = (game_db_data or {}).get("official_accounts", {})
    yt_cid = db_accounts.get("youtube_channel_id")
    social = get_all_social_accounts(game, yt_channel_id=yt_cid, db_accounts=db_accounts)
    results["social_accounts"] = social
    print_social_accounts(social)

    # ── Platform Coverage ─────────────────────────────────────────
    platforms_found = []
    if results.get("steam") and "error" not in results["steam"]:
        platforms_found.append("PC (Steam)")
    if results.get("appstore") and "error" not in results["appstore"]:
        platforms_found.append("iOS")
    if results.get("googleplay") and "error" not in results.get("googleplay", {}) \
            and results.get("googleplay", {}).get("name"):
        platforms_found.append("Android")
    if results.get("taptap") and "error" not in results.get("taptap", {}) \
            and results.get("taptap", {}).get("name"):
        platforms_found.append("TapTap")
    if platforms_found:
        print_section("🖥️  Platform Coverage")
        print(f"  Available on: {' · '.join(platforms_found)}")

    # ── Regional Distribution ─────────────────────────────────────
    print_section("🌍 Regional Distribution")
    gplay_bundle = (results.get("googleplay") or {}).get("app_id") or bundle
    ios_id       = (results.get("appstore") or {}).get("app_id")
    regional = analyze_regional_distribution(
        game, bundle_id=gplay_bundle, appstore_id=ios_id, fast=False
    )
    results["regional"] = regional
    print_regional_distribution(regional)

    # ── Creator Ecosystem ─────────────────────────────────────────
    print_section("🎬 Creator Ecosystem  [YouTube]")
    eco = analyze_creator_ecosystem(game, top_n=20, verbose=False)
    results["creator_ecosystem"] = eco
    total_vids_est = eco.get("video_count_estimate", 0)
    creators = eco.get("top_creators", [])
    mega   = [c for c in creators if c["subscribers"] and c["subscribers"] >= 1_000_000]
    macro  = [c for c in creators if c["subscribers"] and 100_000 <= c["subscribers"] < 1_000_000]
    mid    = [c for c in creators if c["subscribers"] and 10_000 <= c["subscribers"] < 100_000]
    micro  = [c for c in creators if c["subscribers"] and c["subscribers"] < 10_000]
    tiers  = []
    if mega:  tiers.append(f"Mega 1M+ × {len(mega)}")
    if macro: tiers.append(f"Macro 100K-1M × {len(macro)}")
    if mid:   tiers.append(f"Mid 10K-100K × {len(mid)}")
    if micro: tiers.append(f"Micro <10K × {len(micro)}")
    print(f"  Total YouTube videos (est): ~{fmt_num(total_vids_est)}")
    if tiers:
        print(f"  Creator tiers: {' | '.join(tiers)}")
    print()
    print(f"  {'#':<4} {'Channel':<35} {'Subscribers':<12} {'Country':<8} {'Link'}")
    print(f"  {'─'*4} {'─'*35} {'─'*12} {'─'*8} {'─'*40}")
    for i, c in enumerate(creators[:20], 1):
        subs    = fmt_num(c["subscribers"]) if c["subscribers"] else "Hidden"
        name    = c["channel_name"][:34]
        country = c.get("country", "—")
        link    = c.get("url", f"https://youtube.com/channel/{c.get('channel_id','')}")
        print(f"  {i:<4} {name:<35} {subs:<12} {country:<8} {link}")

    # ── Comment Deep Analysis ─────────────────────────────────────
    comment_channel = getattr(args, "comment_channel", None)
    if not comment_channel and game_db_data:
        comment_channel = (game_db_data.get("official_accounts") or {}).get("youtube_channel_id")
    comment_reddit = getattr(args, "comment_reddit", None)

    if comment_channel or comment_reddit:
        print_section(f"💬 Player Deep Analysis")
        if comment_channel:
            yt_kw = analyze_youtube_comments(comment_channel, game, max_videos=10)
            results["yt_comment_analysis"] = yt_kw
            print_deep_analysis("YouTube Comments", yt_kw)
        if comment_reddit:
            rd_kw = analyze_reddit_comments(comment_reddit, game)
            results["reddit_comment_analysis"] = rd_kw
            print_deep_analysis("Reddit", rd_kw)

    print(f"\n{'═'*50}")
    print(f"  ✅ Benchmark complete: {game}")
    print(f"{'═'*50}\n")

    if getattr(args, "output", None):
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Raw data saved to: {args.output}")

    # ── Generate HTML report + upload ─────────────────────────────
    if not getattr(args, "no_html", False):
        try:
            html_path = save_report(game, results)
            print(f"🌐 HTML report saved: {html_path}")
            # Auto-publish via Cloudflare Tunnel
            public_url = publish_report(html_path, game)
            if public_url:
                print(f"\n🔗 Public link: {public_url}")
                results["public_url"] = public_url
        except Exception as e:
            print(f"⚠️  HTML report failed: {e}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game Benchmark v3 — Full Platform Research")
    parser.add_argument("--game",           required=True, help="Game name")
    parser.add_argument("--steam-id",       help="Steam AppID")
    parser.add_argument("--bundle",         help="Google Play bundle ID")
    parser.add_argument("--taptap-id",      help="TapTap game ID")
    parser.add_argument("--reddit",         help="Reddit subreddit name (without r/)")
    parser.add_argument("--tiktok",         help="TikTok hashtag (without #)")
    parser.add_argument("--twitter",        help="Twitter search query")
    parser.add_argument("--youtube",        help="YouTube search query override")
    parser.add_argument("--twitch",         help="Twitch game name override")
    parser.add_argument("--db-game",        help="Key in games_db.json for official account lookup")
    parser.add_argument("--auto-discover",  action="store_true")
    parser.add_argument("--save-discovery", action="store_true")
    parser.add_argument("--comment-channel", help="YouTube channel ID for deep comment analysis")
    parser.add_argument("--comment-reddit",  help="Subreddit for deep comment analysis")
    parser.add_argument("--output",         help="Save raw JSON to file")
    parser.add_argument("--no-html",        action="store_true", help="Skip HTML report generation")
    args = parser.parse_args()
    run_benchmark(args)
