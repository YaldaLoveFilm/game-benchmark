# Game Benchmark Skill - 问题分析

## 问题描述

**Marathon 案例暴露的问题：**

1. **名称歧义处理不当** - "Marathon" 既是游戏名又是马拉松赛事
2. **平台自动发现失败** - 错误匹配到移动应用（Destiny 2 Companion, 2026 LA Marathon）
3. **参数依赖过强** - 需要手动指定精确参数才能正确工作

## 代码结构

```
benchmark-skill/
├── SKILL.md                    # 技能描述文件
├── README.md                   # 本文件
├── games_db.json              # 游戏数据库
└── scripts/
    ├── benchmark_all.py       # 主入口（19195 行）
    ├── quick_benchmark.py     # 快速启动（依赖 games_db.json）
    ├── discover_accounts.py   # 自动发现账号（9949 行）
    ├── comment_keywords.py    # 评论分析（14054 行）
    ├── creator_ecosystem.py   # 创作者生态（6535 行）
    ├── steam_benchmark.py     # Steam 数据
    ├── appstore_benchmark.py  # App Store 数据
    ├── googleplay_benchmark.py # Google Play 数据
    ├── youtube_benchmark.py   # YouTube 数据
    ├── twitter_benchmark.py   # Twitter/X 数据
    ├── reddit_benchmark.py    # Reddit 数据
    ├── tiktok_benchmark.py    # TikTok 数据
    ├── twitch_benchmark.py    # Twitch 数据
    ├── taptap_benchmark.py    # TapTap 数据
    └── intel/
        ├── html_report.py     # HTML 报告生成
        ├── publish.py         # GitHub Pages 发布
        ├── top_videos.py      # 热门视频分析
        ├── regional_distribution.py # 区域分布
        └── __init__.py
    └── social/
        ├── social_accounts.py # 社交账号发现
        └── __init__.py
```

## 关键问题文件

### 1. `quick_benchmark.py` - 自动发现逻辑缺陷
```python
# 问题：依赖 games_db.json，当游戏不在数据库中时触发 --auto-discover
# 自动发现使用简单关键词搜索，无法区分同名实体
```

### 2. `discover_accounts.py` - 搜索逻辑问题
```python
# 问题：使用 Tavily API 搜索，返回最相关结果但不一定是游戏
# 无法过滤掉非游戏实体（如马拉松赛事、加油站应用等）
```

### 3. `benchmark_all.py` - 参数处理问题
```python
# 问题：需要太多手动参数
# 应该能自动识别平台类型（PC/移动/主机）
```

## 复现问题的命令

```bash
# 错误的方式（自动发现失败）
python3 quick_benchmark.py "Marathon"

# 正确的方式（需要手动指定参数）
python3 benchmark_all.py --game "Marathon (Bungie 2026)" --steam-id 3065800 --youtube "Marathon Bungie"
```

## 建议的改进

1. **游戏类型识别** - 根据关键词/数据库判断是 PC/移动/主机游戏
2. **歧义检测** - 检测名称歧义并提示用户澄清
3. **平台智能匹配** - 根据游戏类型自动选择正确的平台 API
4. **失败回退机制** - 当自动发现失败时，提供手动参数选项

## 依赖项

- `google-play-scraper` - Google Play 数据
- `requests` - HTTP 请求
- `youtube-data-api` - YouTube API
- `tavily-python` - 网页搜索
- `steam-web-api` - Steam API