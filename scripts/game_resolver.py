"""
game_resolver.py — 游戏名称消歧 + 元数据补全模块

这是整个改进方案的核心：将用户的模糊输入解析为结构化的 GameProfile，
后续所有模块都基于 GameProfile 工作，不再各自猜测。

解析策略（按优先级）：
1. 精确匹配 games_db.json（canonical_name 或 aliases）
2. 别名模糊匹配（相似度 > 0.75）
3. Web 搜索 + 交叉验证（调用 Tavily API）
4. 置信度不足时请求用户确认

用法：
    resolver = GameResolver("games_db.json")
    profile = resolver.resolve("Genshin Impact")
    print(profile.canonical_name)   # "Genshin Impact"
    print(profile.developer)        # "miHoYo"
    print(profile.confidence)       # 1.0
"""

from __future__ import annotations

import json
import difflib
import sys
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


# ============================================================
# GameProfile — 统一数据结构
# ============================================================
@dataclass
class GameProfile:
    """
    解析后的游戏档案。

    这是后续所有模块的通用输入：
    - platform_router.py 根据 platforms 决定跑哪些脚本
    - search_strategy.py 根据 social_keywords 生成搜索词
    - discover_accounts_v2.py 根据 known_accounts 做交叉验证
    """
    canonical_name: str
    search_name: str              # 用于通用搜索的安全名称
    developer: str = ""
    publisher: str = ""
    platforms: List[str] = field(default_factory=list)
    steam_id: Optional[int] = None
    store_ids: dict = field(default_factory=dict)
    genre: List[str] = field(default_factory=list)
    release_status: str = "released"
    release_year: Optional[int] = None
    social_keywords: dict = field(default_factory=dict)
    known_accounts: dict = field(default_factory=dict)
    disambiguation_hints: List[str] = field(default_factory=list)
    confidence: float = 1.0       # 匹配置信度 0.0 ~ 1.0
    source: str = "db"            # "db" | "web_discovered" | "user_manual" | "unresolved"

    def summary(self) -> str:
        """一行摘要，用于确认提示"""
        parts = [self.canonical_name]
        if self.developer:
            parts.append(f"by {self.developer}")
        if self.platforms:
            parts.append(f"[{', '.join(self.platforms)}]")
        parts.append(f"(confidence: {self.confidence:.0%})")
        return " ".join(parts)


# ============================================================
# GameResolver — 核心解析器
# ============================================================
class GameResolver:
    """
    将用户的模糊输入解析为结构化的 GameProfile。

    初始化时加载 games_db.json 并构建别名索引。
    """

    def __init__(self, db_path: str = "games_db.json"):
        self.db = self._load_db(db_path)
        self.alias_index = {}     # alias_lower -> game_id
        self.name_index = {}      # canonical_name_lower -> game_id
        self._build_indexes()

    def _load_db(self, db_path: str) -> dict:
        """加载游戏数据库"""
        if not os.path.exists(db_path):
            print(f"⚠️  数据库文件不存在: {db_path}")
            return {}
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 过滤掉元数据字段（以 _ 开头）
        return {k: v for k, v in data.items() if not k.startswith("_")}

    def _build_indexes(self):
        """构建别名 → 游戏ID 的反向索引"""
        for game_id, info in self.db.items():
            # canonical name
            cn = info.get("canonical_name", "").lower().strip()
            if cn:
                self.name_index[cn] = game_id
                self.alias_index[cn] = game_id

            # all aliases
            for alias in info.get("aliases", []):
                al = alias.lower().strip()
                if al:
                    self.alias_index[al] = game_id

    # --------------------------------------------------------
    # 主入口
    # --------------------------------------------------------
    def resolve(self, user_input: str, developer_hint: str = "") -> GameProfile:
        """
        主入口：用户输入 → GameProfile

        Args:
            user_input: 用户输入的游戏名（可以模糊）
            developer_hint: 可选的开发商提示，用于辅助消歧

        Returns:
            GameProfile，confidence 字段表示匹配可靠度
        """
        query = user_input.strip()
        query_lower = query.lower()

        # ---- 策略 1：精确匹配 ----
        if query_lower in self.alias_index:
            game_id = self.alias_index[query_lower]
            return self._profile_from_db(game_id, confidence=1.0)

        # ---- 策略 1.5：带开发商的精确匹配 ----
        if developer_hint:
            match = self._match_with_developer(query_lower, developer_hint.lower())
            if match:
                return self._profile_from_db(match, confidence=0.95)

        # ---- 策略 2：模糊匹配 ----
        fuzzy_result = self._fuzzy_match(query_lower)
        if fuzzy_result:
            game_id, score = fuzzy_result
            if score > 0.85:
                return self._profile_from_db(game_id, confidence=score)
            elif score > 0.75:
                return self._profile_from_db(game_id, confidence=score * 0.9)

        # ---- 策略 3：Web 搜索发现 ----
        web_profile = self._web_discover(query, developer_hint)
        if web_profile and web_profile.confidence > 0.6:
            return web_profile

        # ---- 策略 4：无法解析 ----
        return GameProfile(
            canonical_name=query,
            search_name=f"{query} video game",
            confidence=0.0,
            source="unresolved",
        )

    def resolve_interactive(self, user_input: str, developer_hint: str = "") -> GameProfile:
        """
        交互式解析：低置信度时请求用户确认。

        适用于 CLI 环境（quick_benchmark_v2.py）。
        """
        profile = self.resolve(user_input, developer_hint)

        if profile.confidence >= 0.8:
            print(f"✅ 识别为: {profile.summary()}")
            return profile

        if profile.confidence >= 0.5:
            return self._confirm_with_user(profile, user_input)

        # 置信度太低，列出候选
        return self._ask_user_to_choose(user_input)

    # --------------------------------------------------------
    # 匹配策略实现
    # --------------------------------------------------------
    def _match_with_developer(self, query_lower: str, dev_lower: str) -> Optional[str]:
        """尝试用游戏名 + 开发商组合匹配"""
        for game_id, info in self.db.items():
            cn = info.get("canonical_name", "").lower()
            dev = info.get("developer", "").lower()
            if query_lower in cn or cn in query_lower:
                if dev_lower in dev or dev in dev_lower:
                    return game_id
        return None

    def _fuzzy_match(self, query_lower: str) -> Optional[Tuple[str, float]]:
        """
        基于 SequenceMatcher 的模糊匹配。

        同时匹配 canonical names 和 aliases，
        返回最高分的 (game_id, score)。
        """
        best_id = None
        best_score = 0.0

        for alias, game_id in self.alias_index.items():
            score = difflib.SequenceMatcher(None, query_lower, alias).ratio()
            if score > best_score:
                best_score = score
                best_id = game_id

        if best_id and best_score > 0.75:
            return (best_id, best_score)
        return None

    def _web_discover(self, query: str, developer_hint: str = "") -> Optional[GameProfile]:
        """
        通过 Web 搜索发现未收录的游戏。

        改进点：不再只搜一次就信了，而是搜索后进行多信号交叉验证。

        依赖 Tavily API（如未安装则跳过）。
        """
        try:
            from tavily import TavilyClient
        except ImportError:
            print("⚠️  tavily-python 未安装，跳过 Web 发现")
            return None

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            print("⚠️  TAVILY_API_KEY 未设置，跳过 Web 发现")
            return None

        try:
            client = TavilyClient(api_key=api_key)

            # 限定搜索为游戏 —— 加 "video game" 约束
            search_query = f'"{query}" video game'
            if developer_hint:
                search_query += f" {developer_hint}"

            results = client.search(search_query, max_results=5)

            if not results or not results.get("results"):
                return None

            # 交叉验证搜索结果
            return self._validate_web_results(query, results["results"])

        except Exception as e:
            print(f"⚠️  Web 搜索失败: {e}")
            return None

    def _validate_web_results(self, query: str, results: list) -> Optional[GameProfile]:
        """
        对 Web 搜索结果进行交叉验证。

        验证信号：
        1. 结果中"game"/"gaming"出现频率
        2. 是否包含已知游戏平台关键词（Steam, PlayStation, Xbox, Nintendo）
        3. 是否有游戏媒体来源（IGN, GameSpot, Kotaku, PC Gamer 等）
        4. 是否有开发商/发行商信息

        至少满足 2/4 个信号才认为可信。
        """
        GAME_SIGNALS = {"game", "gameplay", "trailer", "gaming", "fps", "rpg",
                        "multiplayer", "pvp", "pve", "steam", "playstation",
                        "xbox", "nintendo", "epic games", "developer", "studio"}
        GAME_MEDIA = {"ign.com", "gamespot.com", "kotaku.com", "pcgamer.com",
                      "polygon.com", "eurogamer.net", "rockpapershotgun.com",
                      "destructoid.com", "gematsu.com", "pushsquare.com",
                      "store.steampowered.com"}

        game_signal_count = 0
        platform_signal = False
        media_signal = False
        dev_info = ""

        for r in results:
            text = f"{r.get('title', '')} {r.get('content', '')}".lower()
            url = r.get("url", "").lower()

            # 信号1：游戏关键词
            matches = sum(1 for s in GAME_SIGNALS if s in text)
            if matches >= 3:
                game_signal_count += 1

            # 信号2：游戏平台
            if any(p in text for p in ["steam", "playstation", "ps5", "xbox", "switch", "epic games"]):
                platform_signal = True

            # 信号3：游戏媒体来源
            if any(m in url for m in GAME_MEDIA):
                media_signal = True

            # 信号4：提取开发商信息
            if not dev_info:
                dev_match = re.search(
                    r'(?:developed|developer|studio|made)\s+(?:by\s+)?([A-Z][A-Za-z\s]+?)(?:\.|,|\s+is|\s+and)',
                    r.get("content", "")
                )
                if dev_match:
                    dev_info = dev_match.group(1).strip()

        # 计算总信号分
        score = 0
        if game_signal_count >= 2:
            score += 1
        if platform_signal:
            score += 1
        if media_signal:
            score += 1
        if dev_info:
            score += 1

        if score >= 2:
            confidence = min(0.4 + score * 0.15, 0.85)
            return GameProfile(
                canonical_name=query,
                search_name=f"{query} {dev_info} game" if dev_info else f"{query} video game",
                developer=dev_info,
                confidence=confidence,
                source="web_discovered",
            )

        return None

    # --------------------------------------------------------
    # 交互式确认
    # --------------------------------------------------------
    def _confirm_with_user(self, profile: GameProfile, original_input: str) -> GameProfile:
        """中等置信度时请用户确认"""
        print(f"\n⚠️  '{original_input}' 可能是:")
        print(f"   → {profile.summary()}")
        try:
            answer = input("是否正确？(y/n/输入正确名称): ").strip()
        except (EOFError, KeyboardInterrupt):
            return profile

        if answer.lower() in ("y", "yes", "是"):
            profile.confidence = 1.0
            profile.source = "user_manual"
            return profile
        elif answer.lower() in ("n", "no", "否"):
            return self._ask_user_to_choose(original_input)
        else:
            # 用户输入了新名称，重新解析
            return self.resolve(answer)

    def _ask_user_to_choose(self, original_input: str) -> GameProfile:
        """置信度太低，列出候选供用户选择"""
        candidates = self._find_candidates(original_input)

        if candidates:
            print(f"\n❓ 无法确定 '{original_input}' 对应哪款游戏。")
            print("可能的候选：")
            for i, (game_id, score) in enumerate(candidates[:5], 1):
                info = self.db[game_id]
                dev = info.get("developer", "unknown")
                print(f"  {i}. {info['canonical_name']} (by {dev}) - 匹配度 {score:.0%}")
            print(f"  0. 以上都不是")

            try:
                choice = input("请选择 (数字): ").strip()
            except (EOFError, KeyboardInterrupt):
                return self._fallback_profile(original_input)

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(candidates):
                    game_id = candidates[idx - 1][0]
                    return self._profile_from_db(game_id, confidence=1.0, source="user_manual")

        # 都不是 → 手动输入模式
        print("\n请提供更多信息：")
        print("  格式: 游戏名 --developer 开发商")
        print(f"  例如: Heartopia --developer XD")
        try:
            manual = input("输入: ").strip()
        except (EOFError, KeyboardInterrupt):
            return self._fallback_profile(original_input)

        if "--developer" in manual:
            parts = manual.split("--developer")
            name = parts[0].strip()
            dev = parts[1].strip() if len(parts) > 1 else ""
            return GameProfile(
                canonical_name=name,
                search_name=f"{name} {dev} game",
                developer=dev,
                confidence=0.9,
                source="user_manual",
            )

        return self._fallback_profile(original_input)

    def _find_candidates(self, query: str) -> List[Tuple[str, float]]:
        """查找所有可能匹配的候选，按相似度排序"""
        candidates = []
        query_lower = query.lower()

        for alias, game_id in self.alias_index.items():
            score = difflib.SequenceMatcher(None, query_lower, alias).ratio()
            if score > 0.4:
                # 避免同一游戏重复出现
                if not any(gid == game_id for gid, _ in candidates):
                    candidates.append((game_id, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def _fallback_profile(self, user_input: str) -> GameProfile:
        """最终兜底：返回低置信度 profile"""
        return GameProfile(
            canonical_name=user_input,
            search_name=f"{user_input} video game",
            confidence=0.0,
            source="unresolved",
        )

    # --------------------------------------------------------
    # 从数据库构建 GameProfile
    # --------------------------------------------------------
    def _profile_from_db(
        self,
        game_id: str,
        confidence: float = 1.0,
        source: str = "db",
    ) -> GameProfile:
        """从数据库条目构建 GameProfile"""
        info = self.db[game_id]
        dev = info.get("developer", "")
        name = info.get("canonical_name", game_id)

        # 构建安全搜索名
        if dev:
            search_name = f"{name} {dev} game"
        else:
            search_name = f"{name} game"

        return GameProfile(
            canonical_name=name,
            search_name=search_name,
            developer=dev,
            publisher=info.get("publisher", ""),
            platforms=info.get("platforms", []),
            steam_id=info.get("store_ids", {}).get("steam"),
            store_ids=info.get("store_ids", {}),
            genre=info.get("genre", []),
            release_status=info.get("release_status", "released"),
            release_year=info.get("release_year"),
            social_keywords=info.get("social_search_keywords", {}),
            known_accounts=info.get("known_accounts", {}),
            disambiguation_hints=info.get("disambiguation_hints", []),
            confidence=confidence,
            source=source,
        )

    # --------------------------------------------------------
    # 工具方法
    # --------------------------------------------------------
    def list_games(self) -> List[str]:
        """列出数据库中所有游戏"""
        return [info.get("canonical_name", gid)
                for gid, info in self.db.items()]

    def get_game_count(self) -> int:
        """数据库中的游戏数量"""
        return len(self.db)


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "games_db.json")
    if not os.path.exists(db_path):
        db_path = "games_db.json"

    resolver = GameResolver(db_path)
    print(f"数据库中共 {resolver.get_game_count()} 款游戏\n")

    test_inputs = [
        ("Heartopia", ""),
        ("CS2", ""),
        ("Genshin", ""),
        ("Genshin Impact", "miHoYo"),
        ("Animal Crossing", ""),
        ("SomeRandomGame2026", ""),
        ("原神", ""),
        ("星铁", ""),
    ]

    for user_input, dev_hint in test_inputs:
        profile = resolver.resolve(user_input, dev_hint)
        print(f"Input: '{user_input}'" + (f" (hint: {dev_hint})" if dev_hint else ""))
        print(f"  → {profile.summary()}")
        print(f"  Source: {profile.source}")
        print()
