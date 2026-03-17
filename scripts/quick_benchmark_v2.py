#!/usr/bin/env python3
"""
quick_benchmark_v2.py — 重构后的快速启动入口
 
整合所有改进模块：
  GameResolver  →  搜索词策略  →  平台路由  →  执行  →  报告
 
用法：
  # 最简模式（自动消歧 + 智能路由）
  python quick_benchmark_v2.py "Heartopia"
 
  # 带开发商提示（消除歧义）
  python quick_benchmark_v2.py "Heartopia" --developer XD
 
  # 手动指定参数（跳过自动推断）
  python quick_benchmark_v2.py "Genshin Impact" --steam-id 1971870 --platforms pc ios android
 
  # 强制模式（跳过确认直接运行）
  python quick_benchmark_v2.py "Heartopia" --force
 
  # 只显示执行计划，不实际运行
  python quick_benchmark_v2.py "Counter-Strike 2" --dry-run
 
  # 查看数据库中所有已知游戏
  python quick_benchmark_v2.py --list-games
"""
 
from __future__ import annotations
 
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
 
# 确保 scripts/ 在 import path 中
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
 
from game_resolver import GameResolver, GameProfile
from platform_router import get_execution_plan, get_skipped_scripts, print_execution_plan, ScriptConfig
from search_strategy import build_search_queries
 
 
# ============================================================
# 配置
# ============================================================
DEFAULT_DB_PATH = SCRIPT_DIR.parent / "games_db.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "reports"
 
 
# ============================================================
# 执行引擎
# ============================================================
class BenchmarkExecutor:
    """执行采集脚本并收集结果"""
 
    def __init__(self, script_dir: Path, output_dir: Path):
        self.script_dir = script_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
 
    def run_plan(
        self,
        profile: GameProfile,
        plan: Dict[str, ScriptConfig],
        dry_run: bool = False,
    ) -> Dict[str, dict]:
        """
        执行整个采集计划。
 
        Args:
            profile:  游戏档案
            plan:     执行计划 {script_name: ScriptConfig}
            dry_run:  如果 True，只打印命令不实际执行
 
        Returns:
            {script_name: {"status": ..., "duration": ..., "output": ...}}
        """
        results = {}
        total = len(plan)
 
        print(f"\n{'='*60}")
        print(f"🚀 开始采集: {profile.canonical_name}")
        print(f"   共 {total} 个脚本待执行")
        print(f"{'='*60}")
 
        for i, (script_name, config) in enumerate(plan.items(), 1):
            print(f"\n[{i}/{total}] ▶ {script_name}")
            print(f"   Mode: {config.search_mode}")
            if config.query:
                print(f"   Query: '{config.query}'")
            if config.store_id:
                print(f"   Store ID: {config.store_id}")
 
            if dry_run:
                print(f"   ⏭️  [DRY RUN] 跳过实际执行")
                results[script_name] = {"status": "dry_run", "duration": 0}
                continue
 
            result = self._execute_script(profile, config)
            results[script_name] = result
 
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"   {status_icon} {result['status']} ({result['duration']:.1f}s)")
 
        return results
 
    def _execute_script(self, profile: GameProfile, config: ScriptConfig) -> dict:
        """执行单个采集脚本"""
        script_path = self.script_dir / config.script_name
 
        if not script_path.exists():
            return {
                "status": "not_found",
                "duration": 0,
                "error": f"Script not found: {script_path}",
            }
 
        # 构建命令行参数
        cmd = [sys.executable, str(script_path)]
        cmd.extend(["--game", profile.canonical_name])
 
        if config.search_mode == "id" and config.store_id:
            cmd.extend(["--id", str(config.store_id)])
        elif config.query:
            cmd.extend(["--query", config.query])
 
        # 通用参数
        cmd.extend(["--output-dir", str(self.output_dir)])
 
        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
                cwd=str(self.script_dir),
            )
            duration = time.time() - start
 
            if proc.returncode == 0:
                return {
                    "status": "success",
                    "duration": duration,
                    "stdout": proc.stdout[-2000:] if proc.stdout else "",
                }
            else:
                return {
                    "status": "error",
                    "duration": duration,
                    "error": proc.stderr[-1000:] if proc.stderr else "Unknown error",
                    "returncode": proc.returncode,
                }
 
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "duration": 300,
                "error": "Script exceeded 5-minute timeout",
            }
        except Exception as e:
            return {
                "status": "exception",
                "duration": time.time() - start,
                "error": str(e),
            }
 
 
# ============================================================
# 报告生成
# ============================================================
def generate_summary(
    profile: GameProfile,
    plan: Dict[str, ScriptConfig],
    results: Dict[str, dict],
    skipped: list,
    output_dir: Path,
):
    """生成执行摘要报告"""
    summary = {
        "generated_at": datetime.now().isoformat(),
        "game": {
            "name": profile.canonical_name,
            "developer": profile.developer,
            "publisher": profile.publisher,
            "platforms": profile.platforms,
            "genre": profile.genre,
            "release_status": profile.release_status,
        },
        "resolver": {
            "confidence": profile.confidence,
            "source": profile.source,
        },
        "execution": {
            "total_scripts": len(plan),
            "successful": sum(1 for r in results.values() if r.get("status") == "success"),
            "failed": sum(1 for r in results.values() if r.get("status") in ("error", "exception")),
            "skipped_scripts": skipped,
        },
        "results": {
            name: {
                "status": r.get("status"),
                "duration": r.get("duration", 0),
                "error": r.get("error"),
            }
            for name, r in results.items()
        },
    }
 
    # 写入 JSON 摘要
    summary_path = output_dir / f"{_safe_filename(profile.canonical_name)}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
 
    # 打印摘要
    print(f"\n{'='*60}")
    print(f"📋 执行摘要")
    print(f"{'='*60}")
    print(f"游戏: {profile.canonical_name} (by {profile.developer})")
    print(f"解析置信度: {profile.confidence:.0%} (来源: {profile.source})")
    print(f"脚本总数: {len(plan)}")
 
    success = summary["execution"]["successful"]
    failed = summary["execution"]["failed"]
    print(f"成功: {success}  失败: {failed}  跳过: {len(skipped)}")
 
    if failed > 0:
        print(f"\n❌ 失败的脚本:")
        for name, r in results.items():
            if r.get("status") in ("error", "exception", "timeout"):
                print(f"  • {name}: {r.get('error', 'unknown')[:100]}")
 
    print(f"\n📁 摘要已保存: {summary_path}")
    return summary_path
 
 
def _safe_filename(name: str) -> str:
    """生成安全的文件名"""
    import re
    safe = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()
    return safe[:50]
 
 
# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Game Benchmark v2 — 智能竞品游戏资讯采集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "Heartopia"                       # 自动识别 + 智能路由
  %(prog)s "Heartopia" --developer XD        # 带开发商消歧
  %(prog)s "CS2" --dry-run                   # 只看计划不执行
  %(prog)s --list-games                      # 查看数据库
        """,
    )
 
    parser.add_argument("game", nargs="?", help="游戏名称（支持模糊输入）")
    parser.add_argument("--developer", "-d", help="开发商名称（辅助消歧）")
    parser.add_argument("--steam-id", type=int, help="手动指定 Steam ID")
    parser.add_argument("--platforms", nargs="+", help="手动指定平台 (pc, ps5, xbox, switch, ios, android)")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="游戏数据库路径")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--force", "-f", action="store_true", help="跳过确认直接运行")
    parser.add_argument("--dry-run", action="store_true", help="只显示执行计划，不实际运行")
    parser.add_argument("--list-games", action="store_true", help="列出数据库中所有游戏")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
 
    args = parser.parse_args()
 
    # -- 列出游戏 --
    if args.list_games:
        resolver = GameResolver(args.db)
        games = resolver.list_games()
        print(f"数据库中共 {len(games)} 款游戏:\n")
        for g in sorted(games):
            print(f"  • {g}")
        return
 
    if not args.game:
        parser.error("请指定游戏名称，或使用 --list-games 查看数据库")
 
    # ===== Phase 1: Resolve =====
    print(f"🔍 正在解析: '{args.game}'")
    resolver = GameResolver(args.db)
 
    if args.force:
        profile = resolver.resolve(args.game, developer_hint=args.developer or "")
    else:
        profile = resolver.resolve_interactive(args.game, developer_hint=args.developer or "")
 
    # 用户手动参数覆盖自动推断
    if args.steam_id:
        profile.steam_id = args.steam_id
        profile.store_ids = profile.store_ids or {}
        profile.store_ids["steam"] = args.steam_id
        if profile.confidence < 1.0:
            profile.confidence = max(profile.confidence, 0.9)
            profile.source = "user_manual"
 
    if args.platforms:
        profile.platforms = args.platforms
        if profile.confidence < 1.0:
            profile.confidence = max(profile.confidence, 0.8)
 
    # 置信度检查
    if profile.confidence < 0.5 and not args.force:
        print(f"\n⚠️  置信度过低 ({profile.confidence:.0%})，建议提供更多信息:")
        print(f"  --developer <开发商名称>")
        print(f"  --steam-id <Steam App ID>")
        print(f"  --platforms pc ps5 xbox")
        print(f"\n或使用 --force 强制运行")
        sys.exit(1)
 
    # ===== Phase 2: Route =====
    plan = get_execution_plan(profile)
    skipped = get_skipped_scripts(profile)
 
    # 显示执行计划
    print_execution_plan(profile)
 
    if not args.force and not args.dry_run:
        try:
            confirm = input(f"\n确认执行 {len(plan)} 个脚本？(y/n): ").strip()
            if confirm.lower() not in ("y", "yes", "是"):
                print("已取消")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return
 
    # ===== Phase 3: Execute =====
    output_dir = Path(args.output_dir)
    executor = BenchmarkExecutor(script_dir=SCRIPT_DIR, output_dir=output_dir)
    results = executor.run_plan(profile, plan, dry_run=args.dry_run)
 
    # ===== Phase 4: Report =====
    summary_path = generate_summary(profile, plan, results, skipped, output_dir)
 
    print(f"\n🏁 完成！")
 
 
if __name__ == "__main__":
    main()
