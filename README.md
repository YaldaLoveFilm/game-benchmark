# 🎮 Game Benchmark

Multi-platform competitive game intelligence tool. Generates structured 13-chapter research briefs covering App Store, Google Play, Steam, YouTube, TikTok, Reddit, Twitter/X, Twitch, and TapTap.

**Sample output:** [Heartopia 竞品简报](https://yaldalovefilm.github.io/game-benchmark-reports/Heartopia_brief_20260317.html)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run benchmark for any game
python scripts/quick_benchmark_v2.py "Heartopia"

# With developer hint for disambiguation
python scripts/quick_benchmark_v2.py "Heartopia" --developer XD

# Preview execution plan without running
python scripts/quick_benchmark_v2.py "Counter-Strike 2" --dry-run

# List all games in local database
python scripts/quick_benchmark_v2.py --list-games
```

---

## Output Structure (13 Chapters)

Every report follows this standard structure:

| # | Chapter | Data Sources |
|---|---------|-------------|
| ⚡ | **Key Conclusions (TL;DR)** — always first | Synthesized |
| 1 | Game Info | Manual / Web |
| 2 | Downloads & Platform Distribution | App Store, Google Play, SteamDB |
| 3 | Regional User Distribution | App Store regional ratings (proxy) |
| 4 | Official Social Accounts | Twitter, YouTube, TikTok, Discord, Reddit |
| 5 | Media Coverage | Web search |
| 6 | Recent LiveOps Updates | Patch notes, official channels |
| 7 | YouTube Creator Ecosystem | YouTube Data API |
| 8 | TikTok Content Ecosystem | TikTok / Douyin |
| 9 | Top 5 Videos | YouTube Data API |
| 10 | Community Sentiment | Reddit, Twitter, YouTube comments |
| 11 | Core Player Profile | Synthesized |
| 12 | Competitive Positioning | Synthesized |
| 13 | Summary | Synthesized |

> **Key rules baked in:**
> - Key conclusions always come first (not last)
> - Regional downloads always include estimated numbers (not just "high/medium/low")
> - All links must be clickable
> - Missing data is marked as `Estimated` or `No public data`, never skipped

---

## Project Structure

```
game-benchmark/
├── SKILL.md                    # AI agent instructions
├── PROMPT_TEMPLATE.md          # 13-chapter report template
├── README.md                   # This file
├── games_db.json               # Known games database
├── requirements.txt
└── scripts/
    ├── quick_benchmark_v2.py   # Main entry point
    ├── benchmark_all.py        # Full pipeline runner
    ├── game_resolver.py        # Name disambiguation + metadata
    ├── search_strategy.py      # Safe per-platform query generation
    ├── platform_router.py      # Intelligent platform routing
    ├── discover_accounts_v2.py # Cross-validated social account discovery
    │
    ├── appstore_benchmark.py   # App Store data
    ├── googleplay_benchmark.py # Google Play data
    ├── steam_benchmark.py      # Steam data
    ├── youtube_benchmark.py    # YouTube data
    ├── tiktok_benchmark.py     # TikTok data
    ├── reddit_benchmark.py     # Reddit data
    ├── twitter_benchmark.py    # Twitter/X data
    ├── twitch_benchmark.py     # Twitch data
    ├── taptap_benchmark.py     # TapTap data
    │
    └── intel/
        ├── html_report.py      # Themed HTML report generator
        ├── publish.py          # GitHub Pages auto-publish
        ├── top_videos.py       # Popular video analysis
        └── regional_distribution.py
```

---

## Environment Variables

```bash
YOUTUBE_API_KEY=...       # YouTube Data API v3
STEAM_API_KEY=...         # Steam Web API
TAVILY_API_KEY=...        # Tavily search (web discovery)
GITHUB_TOKEN=...          # GitHub Pages publishing (optional)
```

---

## Dependencies

```
google-play-scraper   # Google Play data
requests              # HTTP
tavily-python         # Web search for auto-discovery
app-store-scraper     # App Store data
```
