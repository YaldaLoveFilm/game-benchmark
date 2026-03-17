"""
discover_accounts_v2.py — 社交账号发现（交叉验证版）

多信号交叉验证，避免将非游戏账号误识别为官方账号：
1. 名称匹配 — 账号名是否包含游戏名/开发商名
2. 内容相关 — 账号内容是否包含游戏关键词
3. 官方链接 — 账号是否链接到已知官方资源
4. 跨平台引用 — 已验证的账号之间是否互相引用

至少 2/4 个信号通过才采信。

用法：
    discoverer = AccountDiscoverer()
    accounts = discoverer.discover(profile)
"""

from __future__ import annotations
import re
import os
from typing import TYPE_CHECKING, Dict, List, Optional
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from game_resolver import GameProfile


# ============================================================
# DiscoveredAccount — 单个发现的账号
# ============================================================
@dataclass
class DiscoveredAccount:
    """一个被发现的社交账号"""
    platform: str               # youtube, twitter, reddit, ...
    url: str
    name: str = ""
    description: str = ""
    recent_content: str = ""    # 最近发布内容摘要
    follower_count: int = 0

    # 验证相关
    verification_score: int = 0
    verification_reasons: List[str] = field(default_factory=list)
    is_verified: bool = False


# ============================================================
# 验证信号常量
# ============================================================
GAME_CONTENT_SIGNALS = {
    "game", "gameplay", "trailer", "update", "patch", "beta",
    "fps", "pvp", "pve", "multiplayer", "dlc", "season",
    "release", "launch", "demo", "playtest", "early access",
    "dev", "developer", "studio", "gaming",
}

NON_GAME_SIGNALS = {
    # 运动/体育类歧义词
    "5k", "10k", "finish line", "personal best", "race day",
    "running shoes", "26.2 miles",
    # 工业/IT 类歧义词
    "remote control", "control systems", "access control",
    "control panel", "quality control",
    # 通用非游戏内容
    "fitness", "workout", "recipe", "cooking", "fashion",
}

GAME_MEDIA_DOMAINS = {
    "store.steampowered.com", "epicgames.com", "playstation.com",
    "xbox.com", "nintendo.com", "ign.com", "gamespot.com",
    "kotaku.com", "pcgamer.com", "polygon.com",
}


# ============================================================
# AccountDiscoverer — 主类
# ============================================================
class AccountDiscoverer:
    """
    改进后的社交账号发现器。

    核心改变：不再相信单一搜索结果，
    而是用多个信号交叉验证。
    """

    def __init__(self, tavily_api_key: str = None):
        self.api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY", "")

    def discover(self, profile: "GameProfile") -> Dict[str, List[DiscoveredAccount]]:
        """
        主入口：发现并验证社交账号。

        优先使用 GameProfile 中预置的 known_accounts，
        缺少的平台再通过搜索发现。

        Returns:
            {platform: [DiscoveredAccount, ...]}
        """
        result = {}

        # 步骤1：先用已知账号（来自 games_db.json）
        known = getattr(profile, "known_accounts", {}) or {}
        for platform, accounts in known.items():
            result[platform] = [
                DiscoveredAccount(
                    platform=platform,
                    url=acc if acc.startswith("http") else f"https://{platform}.com/{acc.lstrip('@')}",
                    name=acc,
                    verification_score=4,
                    verification_reasons=["known_from_db"],
                    is_verified=True,
                )
                for acc in accounts
            ]

        # 步骤2：搜索未覆盖的平台
        target_platforms = ["youtube", "twitter", "reddit", "tiktok", "twitch"]
        missing = [p for p in target_platforms if p not in result]

        if missing and self.api_key:
            discovered = self._search_platforms(profile, missing)
            # 步骤3：交叉验证
            verified = self._cross_validate(discovered, profile, result)
            result.update(verified)

        return result

    # --------------------------------------------------------
    # 搜索
    # --------------------------------------------------------
    def _search_platforms(
        self,
        profile: "GameProfile",
        platforms: List[str],
    ) -> Dict[str, List[DiscoveredAccount]]:
        """用 Tavily 搜索各平台的官方账号"""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
        except ImportError:
            print("⚠️  tavily-python 未安装")
            return {}

        candidates = {}
        safe_name = self._safe_search_name(profile)

        for platform in platforms:
            query = self._build_search_query(safe_name, platform, profile)
            try:
                results = client.search(query, max_results=5)
                accounts = self._parse_search_results(results, platform)
                if accounts:
                    candidates[platform] = accounts
            except Exception as e:
                print(f"  ⚠️  搜索 {platform} 失败: {e}")

        return candidates

    def _safe_search_name(self, profile: "GameProfile") -> str:
        """生成安全的搜索名"""
        name = profile.canonical_name
        dev = profile.developer
        if dev:
            return f"{name} {dev} game"
        return f"{name} video game"

    def _build_search_query(self, safe_name: str, platform: str, profile: "GameProfile") -> str:
        """为特定平台构建搜索查询"""
        # 优先使用预置的搜索关键词
        social_kw = getattr(profile, "social_keywords", {}) or {}
        base = social_kw.get(platform, safe_name)

        templates = {
            "youtube":  f"{base} official YouTube channel",
            "twitter":  f"{base} official Twitter account",
            "reddit":   f"{base} subreddit reddit",
            "tiktok":   f"{base} official TikTok",
            "twitch":   f"{base} Twitch channel",
        }
        return templates.get(platform, f"{base} {platform} official")

    def _parse_search_results(
        self, results: dict, platform: str,
    ) -> List[DiscoveredAccount]:
        """从搜索结果中提取候选账号"""
        if not results or not results.get("results"):
            return []

        accounts = []
        for r in results["results"]:
            url = r.get("url", "")
            title = r.get("title", "")
            content = r.get("content", "")

            # 基本 URL 过滤：确保结果来自对应平台
            platform_domains = {
                "youtube":  ["youtube.com", "youtu.be"],
                "twitter":  ["twitter.com", "x.com"],
                "reddit":   ["reddit.com"],
                "tiktok":   ["tiktok.com"],
                "twitch":   ["twitch.tv"],
            }
            domains = platform_domains.get(platform, [])
            if not any(d in url.lower() for d in domains):
                continue

            accounts.append(DiscoveredAccount(
                platform=platform,
                url=url,
                name=title,
                description=content[:500],
                recent_content=content[500:1000] if len(content) > 500 else "",
            ))

        return accounts

    # --------------------------------------------------------
    # 交叉验证（核心改进）
    # --------------------------------------------------------
    def _cross_validate(
        self,
        candidates: Dict[str, List[DiscoveredAccount]],
        profile: "GameProfile",
        already_verified: Dict[str, List[DiscoveredAccount]],
    ) -> Dict[str, List[DiscoveredAccount]]:
        """
        多信号交叉验证。

        每个候选账号需要至少 2/4 个信号通过：
        1. 名称匹配
        2. 内容相关
        3. 官方链接
        4. 跨平台引用
        """
        verified = {}

        for platform, accounts in candidates.items():
            platform_verified = []

            for account in accounts:
                score = 0
                reasons = []

                # 信号1：名称匹配
                if self._check_name_match(account, profile):
                    score += 1
                    reasons.append("name_match")

                # 信号2：内容相关
                content_check = self._check_content_relevance(account, profile)
                if content_check > 0:
                    score += 1
                    reasons.append("content_relevant")
                elif content_check < 0:
                    score -= 1  # 反向信号：明显不相关
                    reasons.append("NEGATIVE: non-game content detected")

                # 信号3：官方链接
                if self._check_official_links(account, profile):
                    score += 1
                    reasons.append("official_link")

                # 信号4：跨平台引用
                if self._check_cross_reference(account, already_verified):
                    score += 1
                    reasons.append("cross_platform_ref")

                # 阈值判断
                account.verification_score = score
                account.verification_reasons = reasons

                if score >= 2:
                    account.is_verified = True
                    platform_verified.append(account)
                    print(f"  ✅ 验证通过: {account.url} (分数 {score}/4: {reasons})")
                else:
                    print(f"  ❌ 排除: {account.url} (分数 {score}/4: {reasons})")

            if platform_verified:
                verified[platform] = platform_verified

        return verified

    # --------------------------------------------------------
    # 四个验证信号
    # --------------------------------------------------------
    def _check_name_match(self, account: DiscoveredAccount, profile: "GameProfile") -> bool:
        """信号1：账号名/简介中包含游戏名或开发商名"""
        text = f"{account.name} {account.description}".lower()
        game_name = profile.canonical_name.lower()
        dev_name = profile.developer.lower() if profile.developer else ""

        # 游戏名匹配
        if game_name in text:
            return True
        # 开发商名匹配
        if dev_name and dev_name in text:
            return True
        # 别名匹配（如果可访问 db）
        return False

    def _check_content_relevance(self, account: DiscoveredAccount, profile: "GameProfile") -> int:
        """
        信号2：内容是否与游戏相关。

        返回值：
          +1 = 相关
           0 = 不确定
          -1 = 明显不相关（包含反向信号）
        """
        text = f"{account.description} {account.recent_content}".lower()

        # 检查反向信号（非游戏内容）
        non_game_hits = sum(1 for s in NON_GAME_SIGNALS if s in text)
        if non_game_hits >= 2:
            return -1

        # 检查正向信号（游戏内容）
        game_hits = sum(1 for s in GAME_CONTENT_SIGNALS if s in text)

        # 额外检查：游戏类型关键词
        genre_hits = sum(1 for g in profile.genre if g.replace("-", " ") in text)

        total_positive = game_hits + genre_hits
        if total_positive >= 3:
            return 1
        return 0

    def _check_official_links(self, account: DiscoveredAccount, profile: "GameProfile") -> bool:
        """信号3：账号描述中是否包含官方游戏链接"""
        text = f"{account.description} {account.recent_content}".lower()

        # 检查是否链接到游戏商店页面
        if profile.steam_id and f"store.steampowered.com/app/{profile.steam_id}" in text:
            return True

        # 检查是否链接到游戏媒体
        for domain in GAME_MEDIA_DOMAINS:
            if domain in text and profile.canonical_name.lower() in text:
                return True

        # 检查是否有官网链接
        dev_domain_hints = [
            profile.developer.lower().replace(" ", ""),
            profile.publisher.lower().replace(" ", "") if profile.publisher else "",
        ]
        for hint in dev_domain_hints:
            if hint and hint in text and len(hint) > 3:
                return True

        return False

    def _check_cross_reference(
        self,
        account: DiscoveredAccount,
        already_verified: Dict[str, List[DiscoveredAccount]],
    ) -> bool:
        """信号4：已验证的账号是否引用了这个候选账号"""
        account_identifiers = [
            account.url.lower(),
            account.name.lower(),
        ]

        for platform, verified_list in already_verified.items():
            for verified_acc in verified_list:
                ref_text = f"{verified_acc.description} {verified_acc.recent_content}".lower()
                for identifier in account_identifiers:
                    if identifier and identifier in ref_text:
                        return True
        return False


# ============================================================
# 报告输出
# ============================================================
def print_discovery_report(
    profile: "GameProfile",
    accounts: Dict[str, List[DiscoveredAccount]],
):
    """打印发现报告"""
    print(f"\n{'='*60}")
    print(f"🔍 Account Discovery Report: {profile.canonical_name}")
    print(f"{'='*60}")

    total = sum(len(v) for v in accounts.values())
    print(f"Found {total} verified accounts across {len(accounts)} platforms\n")

    for platform, accs in sorted(accounts.items()):
        print(f"📱 {platform.upper()}:")
        for acc in accs:
            status = "✅" if acc.is_verified else "⚠️"
            print(f"  {status} {acc.name}")
            print(f"     URL: {acc.url}")
            print(f"     Score: {acc.verification_score}/4 {acc.verification_reasons}")
        print()


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    print("discover_accounts_v2.py — 需要配合 GameProfile 使用")
    print("示例：")
    print("  from game_resolver import GameResolver")
    print("  from discover_accounts_v2 import AccountDiscoverer")
    print("  resolver = GameResolver('games_db.json')")
    print("  profile = resolver.resolve('Heartopia')")
    print("  discoverer = AccountDiscoverer()")
    print("  accounts = discoverer.discover(profile)")
