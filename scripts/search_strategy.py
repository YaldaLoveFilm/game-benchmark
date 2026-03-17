"""
search_strategy.py — 安全搜索词构造模块

核心职责：为每个平台生成不会歧义的搜索关键词。
这是成本最低、收益最高的改进 — 即使没有 Game Resolver，
只要搜索词够精确，就能避免绝大多数误匹配。

用法：
    from search_strategy import build_search_queries
    queries = build_search_queries(profile)
    # {'youtube': 'Genshin Impact miHoYo game', 'steam': None, ...}
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_resolver import GameProfile


# ============================================================
# 常见歧义游戏名 — 单独出现时几乎必然与非游戏实体混淆
# 维护规则：如果一个游戏名在 Google 搜索首页结果中
#           有 >=3 条非游戏结果，就应该加入这个列表
# ============================================================
AMBIGUOUS_NAMES = {
    # 单词名
    "marathon", "control", "prey", "inside", "limbo", "journey",
    "rust", "anthem", "arena", "legends", "fable", "haze",
    "rage", "rime", "soma", "steep", "vigor", "warp",
    "flow", "abzu", "below", "mid", "core", "echo",
    "scorn", "stray", "sifu", "hades", "returnal",
    # 常见短语（仍然歧义）
    "the division", "the crew", "among us", "it takes two",
    "outriders", "extraction", "outlast", "warframe",
    "no man's sky",
}

# ============================================================
# 平台特定的搜索模板
# {query} 会被替换为安全搜索词
# None 表示该平台不走关键词搜索（如 Steam 直接用 ID）
# ============================================================
PLATFORM_QUERY_TEMPLATES = {
    "youtube":     "{query} gameplay trailer",
    "twitter":     "{query}",
    "reddit":      "{query} subreddit game",
    "tiktok":      "{query} gaming",
    "twitch":      "{query}",
    "steam":       None,      # Steam 优先用 store ID，不需要关键词
    "appstore":    "{query}",
    "googleplay":  "{query}",
    "taptap":      "{query}",
}

# 中国发行商列表（TapTap 相关）
CHINESE_PUBLISHERS = {
    "mihoyo", "hoyoverse", "netease", "tencent", "lilith games",
    "yostar", "xd global", "papergames", "dragonest",
    "shanghai hode", "hypergryph", "sunborn network",
}


def build_search_queries(profile: "GameProfile") -> dict:
    """
    为每个平台生成消歧后的搜索关键词。

    优先级：
    1. GameProfile 中预置的 social_keywords（来自 games_db.json）
    2. 自动拼接的安全搜索词

    Args:
        profile: 已解析的游戏档案

    Returns:
        dict: {platform_name: search_query_string}
              值为 None 表示该平台应使用 store ID 而非关键词
    """
    # 如果有预置关键词，先用上
    queries = dict(profile.social_keywords) if profile.social_keywords else {}

    # 自动生成安全搜索词作为兜底
    safe_base = _make_safe_query(profile)

    all_platforms = [
        "youtube", "twitter", "reddit", "tiktok", "twitch",
        "steam", "appstore", "googleplay", "taptap",
    ]

    for platform in all_platforms:
        if platform in queries:
            # 已有预置关键词，跳过
            continue

        # Steam 有 ID 就不用搜索词
        if platform == "steam" and profile.steam_id:
            queries[platform] = None
            continue

        # 用模板包装安全搜索词
        template = PLATFORM_QUERY_TEMPLATES.get(platform, "{query}")
        if template is None:
            queries[platform] = None
        else:
            queries[platform] = template.format(query=safe_base)

    return queries


def _make_safe_query(profile: "GameProfile") -> str:
    """
    构造不会歧义的搜索词。

    策略：
    1. 名称在 AMBIGUOUS_NAMES 中 → 加开发商 + "game"
    2. 短名称（<= 2 词）      → 加 "video game"
    3. 长名称（>= 3 词）       → 直接用（本身就够独特）
    4. 有开发商信息时优先用开发商作消歧词
    """
    name = profile.canonical_name
    name_lower = name.lower().strip()
    words = name.split()

    is_known_ambiguous = name_lower in AMBIGUOUS_NAMES
    is_short = len(words) <= 2

    if is_known_ambiguous and profile.developer:
        return f"{name} {profile.developer} game"
    elif is_known_ambiguous:
        return f"{name} video game"
    elif is_short and profile.developer:
        return f"{name} {profile.developer} game"
    elif is_short:
        return f"{name} game"
    else:
        return name


def get_steam_search_params(profile: "GameProfile") -> dict:
    """
    获取 Steam 平台的搜索参数。

    Steam 支持按 ID 直接查询，比关键词搜索精确得多。
    如果没有 ID，退化为关键词搜索。
    """
    if profile.steam_id:
        return {"mode": "id", "steam_id": profile.steam_id}

    safe_query = _make_safe_query(profile)
    return {"mode": "search", "query": safe_query}


def get_store_search_params(profile: "GameProfile", store: str) -> dict:
    """
    获取移动商店的搜索参数。

    Args:
        store: "appstore" 或 "googleplay"
    """
    store_ids = getattr(profile, "store_ids", {}) or {}
    store_id = store_ids.get(store)

    if store_id:
        return {"mode": "id", "store_id": store_id}

    safe_query = _make_safe_query(profile)
    return {"mode": "search", "query": f"{safe_query} game"}


# ============================================================
# 自测：直接运行此文件可以检验消歧效果
# ============================================================
if __name__ == "__main__":
    from dataclasses import dataclass, field
    from typing import Optional

    @dataclass
    class MockProfile:
        canonical_name: str = ""
        developer: str = ""
        publisher: str = ""
        platforms: list = field(default_factory=list)
        steam_id: Optional[int] = None
        social_keywords: dict = field(default_factory=dict)
        store_ids: dict = field(default_factory=dict)

    test_cases = [
        MockProfile(canonical_name="Genshin Impact", developer="miHoYo"),
        MockProfile(canonical_name="Counter-Strike 2", developer="Valve", steam_id=730),
        MockProfile(canonical_name="Clash Royale", developer="Supercell"),
        MockProfile(canonical_name="Heartopia", developer="XD Entertainment"),
        MockProfile(canonical_name="Control", developer="Remedy Entertainment", steam_id=870780),
    ]

    for p in test_cases:
        queries = build_search_queries(p)
        print(f"\n{'='*60}")
        print(f"Game: {p.canonical_name} (by {p.developer})")
        print(f"Safe base query: {_make_safe_query(p)}")
        for platform, q in sorted(queries.items()):
            status = q if q else "[use store ID]"
            print(f"  {platform:12s} → {status}")
