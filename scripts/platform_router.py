"""
platform_router.py — 智能平台路由模块

根据 GameProfile 中的 platforms、genre、release_status 等信息，
决定应该运行哪些平台采集脚本，避免对不相关的平台浪费 API 调用。

用法：
    from platform_router import get_execution_plan
    plan = get_execution_plan(profile)
    for script, config in plan.items():
        print(f"Run: {script} with query='{config['query']}'")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from game_resolver import GameProfile

from search_strategy import build_search_queries, get_steam_search_params, get_store_search_params


# ============================================================
# 平台 → 采集脚本映射
# ============================================================

# 商店/平台专属脚本
STORE_SCRIPTS = {
    "pc":      ["steam_benchmark.py"],
    "ios":     ["appstore_benchmark.py"],
    "android": ["googleplay_benchmark.py"],
    "switch":  [],     # Nintendo eShop 没有公开 API
    "ps5":     [],
    "ps4":     [],
    "xbox":    [],
}

# 所有游戏都应该覆盖的社交/内容平台
SOCIAL_SCRIPTS = [
    "youtube_benchmark.py",
    "twitter_benchmark.py",
    "reddit_benchmark.py",
    "tiktok_benchmark.py",
    "twitch_benchmark.py",
]

# TapTap 特殊规则：只有中国市场相关的游戏才跑
CHINESE_PUBLISHERS = {
    "mihoyo", "hoyoverse", "netease", "tencent", "lilith games",
    "yostar", "xd global", "papergames", "dragonest",
    "hypergryph", "sunborn network", "shanghaide",
}

CHINESE_FRIENDLY_GENRES = {
    "gacha", "moba", "auto-battler", "idle",
}


# ============================================================
# ScriptConfig — 单个脚本的执行配置
# ============================================================
@dataclass
class ScriptConfig:
    """单个采集脚本的执行配置"""
    script_name: str
    query: Optional[str] = None    # 搜索关键词（None = 用 ID）
    store_id: Optional[str] = None # 商店 ID（如 Steam ID）
    search_mode: str = "search"    # "id" | "search"
    priority: int = 1              # 1=必跑, 2=建议, 3=可选
    reason: str = ""               # 为什么要跑这个脚本

    def summary(self) -> str:
        mode = f"ID={self.store_id}" if self.search_mode == "id" else f"query='{self.query}'"
        return f"{self.script_name} [{mode}] (P{self.priority}: {self.reason})"


# ============================================================
# 核心路由逻辑
# ============================================================
def get_execution_plan(profile: "GameProfile") -> Dict[str, ScriptConfig]:
    """
    根据 GameProfile 生成完整的执行计划。

    返回 {script_name: ScriptConfig} 的有序字典。

    路由规则：
    1. 根据 platforms 字段添加商店脚本
    2. 始终添加社交平台脚本
    3. 根据 publisher/genre 决定是否添加 TapTap
    4. 根据 release_status 调整优先级
    5. 为每个脚本分配正确的搜索参数
    """
    plan = {}
    queries = build_search_queries(profile)

    # ---- 1. 商店脚本（根据平台） ----
    store_scripts_added = set()
    for platform in profile.platforms:
        for script in STORE_SCRIPTS.get(platform, []):
            if script not in store_scripts_added:
                config = _build_store_config(script, profile, queries)
                plan[script] = config
                store_scripts_added.add(script)

    # ---- 2. 社交平台脚本（通用） ----
    for script in SOCIAL_SCRIPTS:
        platform_key = script.replace("_benchmark.py", "")
        query = queries.get(platform_key, profile.search_name)
        plan[script] = ScriptConfig(
            script_name=script,
            query=query,
            search_mode="search",
            priority=1,
            reason=f"Social/content coverage ({platform_key})",
        )

    # ---- 3. TapTap（条件添加） ----
    if _should_run_taptap(profile):
        taptap_query = queries.get("taptap", profile.search_name)
        plan["taptap_benchmark.py"] = ScriptConfig(
            script_name="taptap_benchmark.py",
            query=taptap_query,
            search_mode="search",
            priority=2,
            reason="Chinese market coverage",
        )

    # ---- 4. 未发售游戏的优先级调整 ----
    if profile.release_status == "upcoming":
        plan = _adjust_for_upcoming(plan, profile)

    return plan


def get_skipped_scripts(profile: "GameProfile") -> List[str]:
    """
    列出被跳过的脚本及原因（用于日志/报告）。
    """
    plan = get_execution_plan(profile)
    all_scripts = (
        ["steam_benchmark.py", "appstore_benchmark.py",
         "googleplay_benchmark.py", "taptap_benchmark.py"]
        + SOCIAL_SCRIPTS
    )
    skipped = []
    for script in all_scripts:
        if script not in plan:
            reason = _skip_reason(script, profile)
            skipped.append(f"{script}: {reason}")
    return skipped


# ============================================================
# 内部辅助函数
# ============================================================
def _build_store_config(
    script: str,
    profile: "GameProfile",
    queries: dict,
) -> ScriptConfig:
    """为商店脚本构建配置"""

    if script == "steam_benchmark.py":
        params = get_steam_search_params(profile)
        return ScriptConfig(
            script_name=script,
            query=params.get("query"),
            store_id=str(params.get("steam_id", "")) if params.get("steam_id") else None,
            search_mode=params["mode"],
            priority=1,
            reason="PC store data (Steam)",
        )

    elif script == "appstore_benchmark.py":
        params = get_store_search_params(profile, "appstore")
        return ScriptConfig(
            script_name=script,
            query=params.get("query"),
            store_id=params.get("store_id"),
            search_mode=params["mode"],
            priority=1,
            reason="iOS store data",
        )

    elif script == "googleplay_benchmark.py":
        params = get_store_search_params(profile, "googleplay")
        return ScriptConfig(
            script_name=script,
            query=params.get("query"),
            store_id=params.get("store_id"),
            search_mode=params["mode"],
            priority=1,
            reason="Android store data",
        )

    # 兜底
    platform_key = script.replace("_benchmark.py", "")
    return ScriptConfig(
        script_name=script,
        query=queries.get(platform_key, profile.search_name),
        search_mode="search",
        priority=2,
        reason=f"Store data ({platform_key})",
    )


def _should_run_taptap(profile: "GameProfile") -> bool:
    """判断是否需要跑 TapTap"""
    # 条件1：有安卓平台
    has_android = "android" in profile.platforms

    # 条件2：中国发行商
    pub_lower = profile.publisher.lower()
    dev_lower = profile.developer.lower()
    is_chinese_pub = (
        pub_lower in CHINESE_PUBLISHERS
        or dev_lower in CHINESE_PUBLISHERS
    )

    # 条件3：适合中国市场的类型
    has_cn_genre = bool(set(profile.genre) & CHINESE_FRIENDLY_GENRES)

    # 满足条件1 且（条件2 或 条件3）
    return has_android and (is_chinese_pub or has_cn_genre)


def _adjust_for_upcoming(
    plan: Dict[str, ScriptConfig],
    profile: "GameProfile",
) -> Dict[str, ScriptConfig]:
    """
    未发售游戏的特殊调整：
    - Steam 评论数据不存在 → 降低优先级
    - YouTube/Twitter 预告片讨论更重要 → 提高优先级
    - Twitch 可能有测试直播
    """
    for name, config in plan.items():
        if name == "steam_benchmark.py":
            config.priority = 3
            config.reason += " (upcoming: limited data)"
        elif name in ("youtube_benchmark.py", "twitter_benchmark.py"):
            config.priority = 1
            config.reason += " (upcoming: trailer/hype tracking)"
        elif name == "twitch_benchmark.py":
            config.priority = 2
            config.reason += " (upcoming: beta stream tracking)"
    return plan


def _skip_reason(script: str, profile: "GameProfile") -> str:
    """解释为什么某个脚本被跳过"""
    platform_map = {
        "steam_benchmark.py": "pc",
        "appstore_benchmark.py": "ios",
        "googleplay_benchmark.py": "android",
        "taptap_benchmark.py": "android (Chinese market)",
    }
    needed_platform = platform_map.get(script, "")
    if needed_platform:
        return f"Game not on {needed_platform} (platforms: {profile.platforms})"
    return "Not needed for this game profile"


# ============================================================
# CLI 输出辅助
# ============================================================
def print_execution_plan(profile: "GameProfile"):
    """打印人类可读的执行计划"""
    plan = get_execution_plan(profile)
    skipped = get_skipped_scripts(profile)

    print(f"\n{'='*60}")
    print(f"🎮 {profile.canonical_name}")
    if profile.developer:
        print(f"🏢 Developer: {profile.developer}")
    print(f"🖥️  Platforms: {', '.join(profile.platforms) if profile.platforms else 'unknown'}")
    print(f"📊 Scripts to run: {len(plan)}")
    print(f"{'='*60}")

    # 按优先级分组
    for priority in (1, 2, 3):
        items = [(n, c) for n, c in plan.items() if c.priority == priority]
        if not items:
            continue
        label = {1: "🟢 Must run", 2: "🟡 Recommended", 3: "⚪ Optional"}[priority]
        print(f"\n{label}:")
        for name, config in items:
            print(f"  • {config.summary()}")

    if skipped:
        print(f"\n🔴 Skipped ({len(skipped)}):")
        for s in skipped:
            print(f"  ✗ {s}")


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from game_resolver import GameResolver

    db_path = os.path.join(os.path.dirname(__file__), "..", "games_db.json")
    resolver = GameResolver(db_path)

    test_games = [
        "Marathon",
        "Counter-Strike 2",
        "Genshin Impact",
        "Clash Royale",
        "Animal Crossing",
        "Honkai: Star Rail",
    ]

    for name in test_games:
        profile = resolver.resolve(name)
        print_execution_plan(profile)
        print()
