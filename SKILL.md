---
name: benchmark
description: >
  Comprehensive competitive game intelligence gathering across multiple platforms.
  Use this skill whenever the user wants to benchmark a game, analyze competitor
  game data, gather game market intelligence, or compare games across platforms
  (Steam, YouTube, Twitter/X, Reddit, TikTok, Twitch, App Store, Google Play, TapTap).
  Also trigger when users mention "竞品分析", "game benchmark", "game intelligence",
  "player sentiment", "game market data", or ask about a specific game's performance
  across social/store platforms. Handles ambiguous game names (e.g. "Marathon",
  "Control") through built-in disambiguation.
---

## ⚠️ 输出规则（必须遵守）

### 规则1：关键结论必须前置
每份简报的**第一个区块**必须是 `⚡ 关键结论（TL;DR）`，包含3-5条核心洞察。
不允许把结论放在报告末尾。

### 规则2：地区下载量必须有估算数字
地区分布表格中，下载量不能只写"高/中/低"，必须给出 `Estimated XX万+` 的数字。
估算方法：
- 优先使用 App Store 各区评价数量作为代理指标（评价数 × 100~500 = 粗估下载量）
- 注明信心星级（★★★★☆ = 较可靠，★★☆☆☆ = 粗估）
- 精确数据标注来源，估算数据标注 "Estimated + 估算依据"

### 规则3：所有链接必须可点击
社媒账号、创作者频道、媒体报道、商店页面——全部附带真实URL。
不允许只写平台名称而无链接。

### 规则4：报告结构固定为12章节
参考 PROMPT_TEMPLATE.md 中的标准结构，每次输出必须覆盖全部章节。
无数据时标注 "Estimated" 或 "暂无公开数据"，不允许跳过章节。

# Game Benchmark Skill v2

Gather comprehensive competitive intelligence for any video game across 9 platforms.

## Architecture overview

The skill uses a 4-phase pipeline:

```
User input → Game Resolver → Platform Router → Execute scripts → Generate report
```

### Phase 1: Game Resolver (`scripts/game_resolver.py`)

Resolves ambiguous user input into a structured `GameProfile`:

1. **Exact match** against `games_db.json` canonical names and aliases
2. **Fuzzy match** using SequenceMatcher (threshold: 0.75)
3. **Web discovery** via Tavily API with cross-validation
4. **User confirmation** when confidence is below 0.8

The resolver outputs a `GameProfile` dataclass containing: canonical name, developer,
publisher, platforms, store IDs, genre, social search keywords, and a confidence score.

### Phase 2: Search Strategy (`scripts/search_strategy.py`)

Generates per-platform "safe" search queries that avoid name ambiguity.
For known-ambiguous names (e.g. "Marathon", "Control", "Prey"), it automatically
appends the developer name and "game" to the search query.

### Phase 3: Platform Router (`scripts/platform_router.py`)

Decides which of the 9 platform scripts to run based on:
- `GameProfile.platforms` — PC games skip App Store, mobile games skip Steam
- `GameProfile.genre` — Chinese market games add TapTap
- `GameProfile.release_status` — upcoming games deprioritize store review scripts

### Phase 4: Execution (`scripts/quick_benchmark_v2.py`)

Runs selected scripts with correct search parameters, handles timeouts, and
generates a JSON summary report.

## Quick start

```bash
# Simplest usage — auto-resolve and smart routing
python scripts/quick_benchmark_v2.py "Marathon"

# With developer hint for disambiguation
python scripts/quick_benchmark_v2.py "Marathon" --developer Bungie

# Preview what would run without executing
python scripts/quick_benchmark_v2.py "CS2" --dry-run

# Manual override
python scripts/quick_benchmark_v2.py "Marathon" --steam-id 3065800 --platforms pc ps5 xbox

# List all known games in database
python scripts/quick_benchmark_v2.py --list-games
```

## File structure

```
benchmark-skill/
├── SKILL.md                          # This file
├── README.md                         # Problem analysis
├── games_db.json                     # Game database (v2: with aliases, platforms, social keywords)
├── reports/                          # Generated reports
└── scripts/
    ├── quick_benchmark_v2.py         # NEW: Smart entry point
    ├── game_resolver.py              # NEW: Name disambiguation + metadata
    ├── search_strategy.py            # NEW: Safe search query generation
    ├── platform_router.py            # NEW: Intelligent platform routing
    ├── discover_accounts_v2.py       # NEW: Cross-validated account discovery
    │
    ├── benchmark_all.py              # Original full benchmark (still works)
    ├── quick_benchmark.py            # Original quick start (legacy)
    ├── discover_accounts.py          # Original account discovery (legacy)
    ├── comment_keywords.py           # Comment analysis
    ├── creator_ecosystem.py          # Creator ecosystem analysis
    │
    ├── steam_benchmark.py            # Steam data collection
    ├── appstore_benchmark.py         # App Store data
    ├── googleplay_benchmark.py       # Google Play data
    ├── youtube_benchmark.py          # YouTube data
    ├── twitter_benchmark.py          # Twitter/X data
    ├── reddit_benchmark.py           # Reddit data
    ├── tiktok_benchmark.py           # TikTok data
    ├── twitch_benchmark.py           # Twitch data
    ├── taptap_benchmark.py           # TapTap data
    │
    ├── intel/
    │   ├── html_report.py            # HTML report generation
    │   ├── publish.py                # GitHub Pages publishing
    │   ├── top_videos.py             # Popular video analysis
    │   └── regional_distribution.py  # Regional distribution
    └── social/
        └── social_accounts.py        # Social account management
```

## games_db.json schema (v2)

Each game entry supports:
- `canonical_name` — official game name
- `aliases` — list of alternative names for fuzzy matching
- `developer` / `publisher` — used for disambiguation
- `platforms` — list of platforms (pc, ps5, xbox, switch, ios, android)
- `store_ids` — platform-specific IDs (steam, appstore, googleplay)
- `genre` — genre tags for routing decisions
- `release_status` — "released" or "upcoming"
- `social_search_keywords` — per-platform search queries (pre-disambiguated)
- `known_accounts` — verified official social accounts
- `disambiguation_hints` — what this game is NOT

## Adding a new game to the database

Add an entry to `games_db.json` following the schema above.
At minimum, provide: `canonical_name`, `developer`, `platforms`.
The resolver and router will use these to auto-generate safe search queries
and select the right platform scripts.

## Dependencies

- `google-play-scraper` — Google Play data
- `requests` — HTTP requests
- `tavily-python` — Web search for auto-discovery (optional)
- Standard library: `json`, `difflib`, `dataclasses`, `subprocess`
