# Benchmark Skill v2 迁移说明

## 📋 版本信息

**来源**: GitHub 仓库 `YaldaLoveFilm/benchmark-skill-analysis/tree/main`
**版本**: v2 (完整重构)
**迁移时间**: 2026-03-16 13:08
**备份位置**: `/root/.openclaw/workspace/skills/game-benchmark-backup-20260316_130808/`

## 🎯 核心改进

### 1. 名称消歧系统 (`game_resolver.py`)
- **四级解析策略**: 精确匹配 → 模糊匹配 → Web搜索 → 用户确认
- **置信度评分**: 0.0-1.0 的匹配置信度
- **统一数据结构**: `GameProfile` 贯穿整个流程

### 2. 智能平台路由 (`platform_router.py`)
- **基于平台选择脚本**: PC游戏跳过移动平台，移动游戏包含TapTap
- **优先级系统**: 必跑 > 建议 > 可选
- **中国开发商检测**: 自动为 miHoYo、Netease、Tencent 等添加 TapTap

### 3. 安全搜索策略 (`search_strategy.py`)
- **预消歧搜索词**: 为歧义名称自动添加开发商和"game"后缀
- **平台特定查询**: 为每个平台生成安全的搜索词
- **避免错误匹配**: 防止匹配到非游戏实体（如马拉松赛事、加油站应用）

## 🔧 架构变化

### 旧架构 (v1)
```
用户输入 → quick_benchmark.py → 直接调用平台脚本
```

### 新架构 (v2)
```
用户输入 → GameResolver → SearchStrategy → PlatformRouter → 执行 → 报告
```

### 新核心文件
1. `game_resolver.py` - 名称消歧核心
2. `platform_router.py` - 智能平台路由
3. `search_strategy.py` - 安全搜索策略
4. `quick_benchmark_v2.py` - 新入口点
5. `discover_accounts_v2.py` - 改进的账号发现

## 🧪 解决的问题

### Marathon 歧义案例 (已解决)
**之前的问题**:
- 输入: `Marathon`
- 匹配到: Marathon ARCO Rewards (加油站应用), 2026 LA Marathon (赛事应用)
- 原因: 简单关键词搜索，无法区分同名实体

**现在的解决方案**:
- 输入: `Marathon`
- 解析: 识别为 Bungie 的 Marathon
- 搜索词: `"Marathon Bungie game"`
- 路由: 只运行 PC/主机脚本，跳过移动平台
- 结果: 正确匹配到 Bungie 的游戏

## 📖 使用方式

### 基本用法
```bash
# 自动消歧 + 智能路由
python scripts/quick_benchmark_v2.py "Marathon"

# 带开发商提示
python scripts/quick_benchmark_v2.py "Marathon" --developer Bungie

# 预览执行计划
python scripts/quick_benchmark_v2.py "Marathon" --dry-run

# 手动指定参数
python scripts/quick_benchmark_v2.py "Marathon" --steam-id 3065800 --platforms pc
```

### 高级功能
```bash
# 查看数据库中的游戏
python scripts/quick_benchmark_v2.py --list-games

# 强制运行（跳过确认）
python scripts/quick_benchmark_v2.py "未知游戏" --force

# 只运行特定平台
python scripts/quick_benchmark_v2.py "原神" --platforms ios android
```

## 📊 数据库改进

### 新字段 (games_db.json)
```json
{
  "Marathon": {
    "canonical_name": "Marathon",
    "aliases": ["Marathon Bungie", "Marathon 2026"],
    "developer": "Bungie",
    "platforms": ["pc", "ps5", "xbox"],
    "store_ids": {"steam": 3065800},
    "genre": ["extraction shooter", "pvpve"],
    "release_status": "upcoming",
    "social_search_keywords": {
      "youtube": "Marathon Bungie game",
      "twitter": "Marathon game Bungie",
      "reddit": "r/MarathonTheGame"
    },
    "disambiguation_hints": ["Not Marathon gas station", "Not marathon running event"]
  }
}
```

## 🔄 向后兼容性

### 兼容的功能
- ✅ `quick_benchmark.py` - 旧入口点（保留，但建议使用 v2）
- ✅ `benchmark_all.py` - 完整功能脚本
- ✅ `games_db.json` - 数据库格式兼容
- ✅ 所有平台脚本 - 保持原样

### 不兼容的变化
- ⚠️ `discover_accounts.py` → `discover_accounts_v2.py` (改进版本)
- ⚠️ 自动发现逻辑完全重写
- ⚠️ 参数解析方式改变

## 📦 依赖项

### 必需依赖
- `google-play-scraper` (已安装)
- `requests` (已安装)

### 可选依赖
- `tavily-python` - 用于 Web 发现功能
  ```bash
  pip install tavily-python
  ```

### API Keys (可选)
- YouTube Data API v3 (用于 YouTube 数据分析)
- Tavily API (用于 Web 搜索发现)

## 🚀 性能提升

### 执行效率
- **智能路由**: 减少不必要的 API 调用
- **并行执行**: 支持多脚本并行运行
- **缓存机制**: 重复查询使用缓存结果

### 用户体验
- **清晰反馈**: 显示解析结果和置信度
- **用户指导**: 当置信度低时提供帮助
- **错误处理**: 完善的异常处理和回退机制

## 🔍 测试验证

已通过测试案例:
1. ✅ **Marathon** - 歧义名称消歧
2. ✅ **Control** - 另一个歧义名称
3. ✅ **原神** - 中文游戏，中国开发商检测
4. ✅ **未知游戏** - 正确处理，提供用户指导
5. ✅ **智能路由** - PC/移动平台正确选择

## 📞 技术支持

如果遇到问题:
1. 检查日志: `python scripts/quick_benchmark_v2.py "游戏名" --dry-run`
2. 查看数据库: `cat games_db.json | jq .`
3. 恢复备份: 备份在 `game-benchmark-backup-20260316_130808/`

## 🎉 迁移完成

Benchmark Skill v2 已成功安装并验证！
所有已知问题已解决，特别是 Marathon 的歧义问题。✨