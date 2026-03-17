#!/usr/bin/env python3
"""
生成 Heartopia 竞品简报网页
"""
import os, sys
from pathlib import Path
from datetime import datetime

REPORT_DIR = Path(__file__).parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Heartopia 心动小镇 — 竞品情报简报</title>
<style>
  /* ── 字体 ── */
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
  body {
    font-family: 'Space Grotesk', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, sans-serif;
    background: #100818;
    color: #fdf4ff;
    margin: 0; padding: 0;
    line-height: 1.7;
  }

  /* ── 背景网格渐变 ── */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: -1;
    background:
      radial-gradient(ellipse 80% 60% at 20% 10%, #ff6b9d22 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 80% 80%, #c084fc22 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 60% 30%, #fb923c11 0%, transparent 50%),
      #100818;
  }

  /* ── 顶部 Hero ── */
  .hero {
    padding: 60px 24px 40px;
    text-align: center;
    border-bottom: 1px solid rgba(255,107,157,0.15);
    background: linear-gradient(180deg, rgba(255,107,157,0.08) 0%, transparent 100%);
  }
  .hero-tag {
    display: inline-block;
    background: rgba(255,107,157,0.12);
    border: 1px solid rgba(255,107,157,0.3);
    color: #ff6b9d;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 100px;
    margin-bottom: 20px;
  }
  .hero h1 {
    font-size: clamp(28px, 5vw, 52px);
    font-weight: 700;
    margin: 0 0 12px;
    background: linear-gradient(135deg, #ff6b9d 0%, #c084fc 60%, #fb923c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-meta {
    color: #d8b4fe;
    font-size: 14px;
    opacity: 0.8;
  }

  /* ── 主容器 ── */
  .container {
    max-width: 960px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }

  /* ── TL;DR 卡片 ── */
  .tldr {
    background: linear-gradient(135deg, rgba(255,107,157,0.12) 0%, rgba(192,132,252,0.08) 100%);
    border: 1px solid rgba(255,107,157,0.25);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 40px;
  }
  .tldr-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #ff6b9d;
    margin: 0 0 20px;
  }
  .tldr ol {
    margin: 0; padding: 0 0 0 20px;
  }
  .tldr li {
    margin-bottom: 12px;
    color: #fdf4ff;
    font-size: 15px;
  }
  .tldr li strong { color: #ff6b9d; }

  /* ── Section ── */
  .section {
    margin-bottom: 48px;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,107,157,0.12);
  }
  .section-num {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #ff6b9d, #c084fc);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: #fff;
    flex-shrink: 0;
  }
  .section-title {
    font-size: 18px;
    font-weight: 700;
    color: #fdf4ff;
    margin: 0;
  }

  /* ── 卡片 ── */
  .card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,107,157,0.12);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
  }

  /* ── 表格 ── */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th {
    background: rgba(255,107,157,0.08);
    color: #d8b4fe;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(255,107,157,0.15);
  }
  td {
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #fdf4ff;
    vertical-align: top;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,107,157,0.04); }

  /* ── 徽章 ── */
  .badge {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(255,107,157,0.10);
    border: 1px solid rgba(255,107,157,0.2);
    color: #ff6b9d;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
  }
  .badge.green { background: rgba(74,222,128,0.10); border-color: rgba(74,222,128,0.25); color: #4ade80; }
  .badge.purple { background: rgba(192,132,252,0.12); border-color: rgba(192,132,252,0.25); color: #c084fc; }
  .badge.orange { background: rgba(251,146,60,0.10); border-color: rgba(251,146,60,0.25); color: #fb923c; }
  .badge.red { background: rgba(248,113,113,0.10); border-color: rgba(248,113,113,0.25); color: #f87171; }

  /* ── 数字高亮 ── */
  .stat-row {
    display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px;
  }
  .stat-box {
    flex: 1; min-width: 140px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,107,157,0.12);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
  }
  .stat-num {
    font-size: 26px; font-weight: 700;
    background: linear-gradient(135deg, #ff6b9d, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    line-height: 1.2; margin-bottom: 4px;
  }
  .stat-label {
    font-size: 12px; color: #d8b4fe; opacity: 0.8;
  }

  /* ── 链接 ── */
  a { color: #ff6b9d; text-decoration: none; }
  a:hover { text-decoration: underline; color: #c084fc; }

  /* ── 舆情块 ── */
  .sentiment-block {
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
  }
  .sentiment-block.pos { background: rgba(74,222,128,0.06); border: 1px solid rgba(74,222,128,0.15); }
  .sentiment-block.neg { background: rgba(248,113,113,0.06); border: 1px solid rgba(248,113,113,0.15); }
  .sentiment-block.warn { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.15); }
  .sentiment-block .label {
    font-size: 12px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; margin-bottom: 10px;
  }
  .sentiment-block.pos .label { color: #4ade80; }
  .sentiment-block.neg .label { color: #f87171; }
  .sentiment-block.warn .label { color: #fbbf24; }
  .sentiment-block ul { margin: 0; padding-left: 18px; }
  .sentiment-block li { margin-bottom: 6px; font-size: 14px; }

  /* ── 星级 ── */
  .stars { color: #fbbf24; letter-spacing: 1px; }

  /* ── 页脚 ── */
  footer {
    text-align: center;
    padding: 32px 24px;
    border-top: 1px solid rgba(255,107,157,0.1);
    color: #d8b4fe;
    font-size: 13px;
    opacity: 0.6;
  }

  /* ── 响应式 ── */
  @media (max-width: 600px) {
    .stat-row { gap: 10px; }
    .stat-box { min-width: 120px; }
    .card { padding: 16px; }
    th, td { padding: 8px 10px; }
  }
</style>
</head>
<body>

<!-- Hero -->
<div class="hero">
  <div class="hero-tag">🌸 竞品情报简报</div>
  <h1>Heartopia · 心动小镇</h1>
  <div class="hero-meta">报告日期：2026年3月17日 &nbsp;|&nbsp; 数据来源：App Store · Google Play · SteamDB · 官方新闻稿</div>
</div>

<div class="container">

<!-- TL;DR -->
<div class="tldr">
  <div class="tldr-title">⚡ 关键结论 TL;DR</div>
  <ol>
    <li><strong>日本是最被低估的核心市场</strong> — App Store评价数全球最多（28,141条），评分最高（4.62），VTuber内容生态活跃，本土化投入严重不足</li>
    <li><strong>TikTok营销是成功的关键变量</strong> — 抖音161.6万粉丝+UGC创作激励活动，是同类手游中罕见的短视频营销成功案例</li>
    <li><strong>Android体验是最大产品漏洞</strong> — Google Play仅3.2分（91,587评分），iOS 4.6分，差距显示Android优化严重滞后</li>
    <li><strong>社区危机双杀正在伤害品牌</strong> — 种族歧视动画事件 + Discord管理问题叠加，直接影响北美/欧洲长期增长</li>
    <li><strong>PC端是意外惊喜但天花板明显</strong> — Steam 66K同时在线峰值超预期，但"像移动端移植"的体验评价限制了进一步扩张</li>
  </ol>
</div>

<!-- 1. 基础信息 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">1</div>
    <div class="section-title">游戏基础信息</div>
  </div>
  <div class="card">
    <table>
      <tr><th>字段</th><th>内容</th></tr>
      <tr><td>游戏名称</td><td>Heartopia（心动小镇）</td></tr>
      <tr><td>开发 / 发行商</td><td>XD Entertainment Co., Ltd.（心动网络）</td></tr>
      <tr><td>首次上线</td><td>2026年1月7日（TapTap / iOS / Android）；1月17日（Steam）</td></tr>
      <tr><td>游戏类型</td><td>休闲生活模拟 + 社交沙盒（Cozy Multiplayer Life Sim）</td></tr>
      <tr><td>商业模式</td><td>Free-to-Play + Gacha（装饰性内购）+ 体力系统</td></tr>
      <tr><td>支持平台</td><td><span class="badge green">✅ PC Steam/TapTap</span> <span class="badge green">✅ iOS</span> <span class="badge green">✅ Android</span> <span class="badge red">❌ Console</span></td></tr>
      <tr><td>官方网站</td><td><a href="https://heartopia.xd.com/us/" target="_blank">heartopia.xd.com/us</a></td></tr>
    </table>
  </div>
</div>

<!-- 2. 下载量 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">2</div>
    <div class="section-title">下载量与平台分布</div>
  </div>
  <div class="stat-row">
    <div class="stat-box">
      <div class="stat-num">1,000万+</div>
      <div class="stat-label">全平台总下载（上线21天）</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">66,118</div>
      <div class="stat-label">Steam 同时在线峰值</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">50+</div>
      <div class="stat-label">App Store 登顶国家/地区数</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">240万</div>
      <div class="stat-label">上线3天下载量</div>
    </div>
  </div>
  <table>
    <tr><th>平台</th><th>下载量</th><th>评分</th><th>评价数</th><th>链接</th></tr>
    <tr>
      <td>App Store (iOS)</td>
      <td>Estimated 300万+</td>
      <td><span class="stars">★★★★★</span> 4.6</td>
      <td>22,000+</td>
      <td><a href="https://apps.apple.com/us/app/heartopia/id6746151928" target="_blank">App Store →</a></td>
    </tr>
    <tr>
      <td>Google Play (Android)</td>
      <td><strong>8,195,846次</strong>（实际数据）</td>
      <td><span class="stars">★★★☆☆</span> 3.2</td>
      <td>91,587</td>
      <td><a href="https://play.google.com/store/apps/details?id=com.xd.xdtglobal.gp" target="_blank">Google Play →</a></td>
    </tr>
    <tr>
      <td>Steam (PC)</td>
      <td>Estimated 数十万</td>
      <td>Mixed</td>
      <td>—</td>
      <td><a href="https://store.steampowered.com/app/4025700/Heartopia/" target="_blank">Steam →</a> · <a href="https://steamdb.info/app/4025700/" target="_blank">SteamDB →</a></td>
    </tr>
    <tr>
      <td>TapTap</td>
      <td>—</td>
      <td><span class="stars">★★★★★</span> 8.7/10</td>
      <td>1,500+</td>
      <td><a href="https://www.taptap.io/app/231364" target="_blank">TapTap →</a></td>
    </tr>
  </table>
</div>

<!-- 3. 地区分布 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">3</div>
    <div class="section-title">海外地区用户分布</div>
  </div>
  <p style="font-size:13px;color:#d8b4fe;margin-bottom:16px;">
    📌 估算方法：以 App Store 各区评价数量作代理指标（评价数 × 100~500 = 粗估下载量），精确数据需付费版 SensorTower / AppMagic。
  </p>
  <table>
    <tr><th>地区</th><th>下载量估算</th><th>App Store评分</th><th>评价数</th><th>信心</th><th>备注</th></tr>
    <tr>
      <td>🇯🇵 <strong>日本</strong></td>
      <td><strong>Estimated 200万+</strong></td>
      <td>⭐ 4.62</td>
      <td><strong>28,141</strong> 🔥 全球最多</td>
      <td>★★★★☆</td>
      <td>最核心海外市场，VTuber生态活跃</td>
    </tr>
    <tr>
      <td>🇺🇸 北美</td>
      <td>Estimated 150万+</td>
      <td>⭐ 4.58</td>
      <td>21,807</td>
      <td>★★★★☆</td>
      <td>英语内容产出最多，受争议事件影响</td>
    </tr>
    <tr>
      <td>🇮🇩 东南亚（印尼代表）</td>
      <td>Estimated 80万+</td>
      <td>⭐ 4.69 🏆 最高分</td>
      <td>2,889</td>
      <td>★★★☆☆</td>
      <td>用户满意度最高，增长潜力大</td>
    </tr>
    <tr>
      <td>🇰🇷 韩国</td>
      <td>Estimated 50万+</td>
      <td>⭐ 4.57</td>
      <td>5,517</td>
      <td>★★★☆☆</td>
      <td>—</td>
    </tr>
    <tr>
      <td>🇧🇷 拉美（巴西代表）</td>
      <td>Estimated 40万+</td>
      <td>⭐ 4.64</td>
      <td>3,169</td>
      <td>★★★☆☆</td>
      <td>新兴手游市场</td>
    </tr>
    <tr>
      <td>🇬🇧 欧洲（英国代表）</td>
      <td>Estimated 30万+</td>
      <td>⭐ 4.49 ⚠️ 最低</td>
      <td>2,331</td>
      <td>★★★☆☆</td>
      <td>争议事件影响最明显</td>
    </tr>
    <tr>
      <td>🇩🇪 欧洲（德国）</td>
      <td>Estimated 20万+</td>
      <td>⭐ 4.58</td>
      <td>1,430</td>
      <td>★★☆☆☆</td>
      <td>—</td>
    </tr>
  </table>
</div>

<!-- 4. 社媒账号 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">4</div>
    <div class="section-title">官方社媒账号</div>
  </div>
  <table>
    <tr><th>平台</th><th>账号</th><th>粉丝数</th></tr>
    <tr>
      <td>🎵 抖音 / TikTok</td>
      <td><a href="https://www.douyin.com/user/MS4wLjABAAAAnWeHQqkwGeBunekc1-4wAlfLiaQS3jrK3LtumYY_4IsZnmztb0VmWXa3Aho7yyRw" target="_blank">@xdxzmobile</a></td>
      <td><strong>161.6万</strong>｜点赞 745.9万</td>
    </tr>
    <tr>
      <td>🐦 Twitter / X</td>
      <td><a href="https://twitter.com/MyHeartopia" target="_blank">@MyHeartopia</a></td>
      <td><strong>230,700</strong></td>
    </tr>
    <tr>
      <td>💬 Discord</td>
      <td><a href="https://disboard.org/server/1459649843793363024" target="_blank">官方社区</a></td>
      <td><strong>50万+</strong>（2026年1月）</td>
    </tr>
    <tr>
      <td>📺 YouTube 官方</td>
      <td><a href="https://www.youtube.com/@HeartopiaTW" target="_blank">@HeartopiaTW</a></td>
      <td>25,000 ｜ 129个视频</td>
    </tr>
    <tr>
      <td>📱 Reddit</td>
      <td><a href="https://www.reddit.com/r/heartopia/" target="_blank">r/heartopia</a></td>
      <td>活跃社区</td>
    </tr>
    <tr>
      <td>📷 Instagram</td>
      <td>—</td>
      <td>Estimated 数万</td>
    </tr>
  </table>
</div>

<!-- 5. 媒体报道 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">5</div>
    <div class="section-title">媒体报道</div>
  </div>
  <table>
    <tr><th>媒体</th><th>标题</th></tr>
    <tr><td>Games Press（官方新闻稿）</td><td><a href="https://www.gamespress.com/Cosy-Multiplayer-Life-Sim-Heartopia-Launches-as-No-1-Free-Mobile-Game-" target="_blank">Heartopia Launches as No.1 Free Mobile Game Across 50 Countries →</a></td></tr>
    <tr><td>VG247</td><td><a href="https://www.vg247.com/heartopia-launch-day-record-free-stuff" target="_blank">Heartopia launch day record free stuff →</a></td></tr>
    <tr><td>Pocket Gamer Biz</td><td><a href="https://www.pocketgamer.biz/new-release-roundup-heartopia-cozy-caravan-ichinome-monsters-and-more/" target="_blank">New Release Roundup: Heartopia →</a></td></tr>
    <tr><td>OpenCritic</td><td><a href="https://opencritic.com/news/27528/new-heartopia-fashion-wave-for-march-2026-revealed" target="_blank">Heartopia Fashion Wave for March 2026 →</a></td></tr>
  </table>
  <div class="card" style="margin-top:14px; background: rgba(251,191,36,0.05); border-color: rgba(251,191,36,0.2);">
    ⚠️ <strong style="color:#fbbf24">媒体覆盖空白：</strong>IGN、Polygon、Eurogamer 均无正式评测，主流 Tier-1 游戏媒体几乎缺席，是可以切入的 PR 空间。
  </div>
</div>

<!-- 6. LiveOps -->
<div class="section">
  <div class="section-header">
    <div class="section-num">6</div>
    <div class="section-title">最近3个月 LiveOps 更新</div>
  </div>
  <table>
    <tr><th>时间</th><th>更新内容</th></tr>
    <tr><td>2026年1月</td><td>🌨️ 冰雪季（Snow Season）更新，玩家反应热烈</td></tr>
    <tr><td>2026年1月31日—3月13日</td><td>🎵 抖音「冰雪季创作计划」UGC活动，创作者可瓜分现金 + 专属套装</td></tr>
    <tr><td>2026年2月</td><td>🤝 IP联动：喜羊羊与灰太狼、My Little Pony（小马宝莉）</td></tr>
    <tr><td>2026年3月</td><td>👗 Fashion Wave 时尚活动更新</td></tr>
  </table>
</div>

<!-- 7. YouTube 创作者 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">7</div>
    <div class="section-title">YouTube 创作者生态</div>
  </div>
  <div class="stat-row">
    <div class="stat-box"><div class="stat-num">数百名</div><div class="stat-label">活跃创作者（估算）</div></div>
    <div class="stat-box"><div class="stat-num">数亿次</div><div class="stat-label">总播放量（估算）</div></div>
  </div>
  <table>
    <tr><th>创作者</th><th>频道链接</th><th>内容类型</th></tr>
    <tr><td>🏠 心动小镇官方</td><td><a href="https://www.youtube.com/@HeartopiaTW" target="_blank">@HeartopiaTW →</a></td><td>官方更新、活动预告</td></tr>
    <tr><td>🎮 阿宏游戏实况</td><td>YouTube</td><td>多次直播实况</td></tr>
    <tr><td>🎨 wuliaoleona</td><td>YouTube</td><td>"参观日式房屋"、"大图绘画"</td></tr>
    <tr><td>🦝 Laurent.Sydney 浣熊時尾</td><td>YouTube</td><td>多人合作录播系列</td></tr>
    <tr><td>🐱 日系猫 zisecat</td><td>Twitch / YouTube</td><td>跨平台合作直播</td></tr>
    <tr><td>🌟 欣希亞 Cynia</td><td>YouTube</td><td>台湾VTuber，参观玩家家园</td></tr>
    <tr><td>🐭 吱吱 nezumi_zizi</td><td>YouTube</td><td>"你家长怎样？" 高互动</td></tr>
    <tr><td>🌍 Psyhodelik</td><td>YouTube</td><td>"2026年最热门游戏"英语评测</td></tr>
    <tr><td>🎯 PrettyPoison Gaming</td><td>YouTube</td><td>"10 Advanced Tips" 攻略</td></tr>
    <tr><td>📺 Squasha Streams</td><td>YouTube</td><td>"we love heartopia"（7K观看）</td></tr>
  </table>
</div>

<!-- 8. TikTok -->
<div class="section">
  <div class="section-header">
    <div class="section-num">8</div>
    <div class="section-title">TikTok 内容生态</div>
  </div>  <div class="stat-row">
    <div class="stat-box"><div class="stat-num">161.6万</div><div class="stat-label">官方抖音粉丝数</div></div>
    <div class="stat-box"><div class="stat-num">745.9万</div><div class="stat-label">官方抖音点赞数</div></div>
  </div>
  <table>
    <tr><th>指标</th><th>数据</th></tr>
    <tr><td>官方账号</td><td><a href="https://www.douyin.com/user/MS4wLjABAAAAnWeHQqkwGeBunekc1-4wAlfLiaQS3jrK3LtumYY_4IsZnmztb0VmWXa3Aho7yyRw" target="_blank">@xdxzmobile（抖音）→</a></td></tr>
    <tr><td>主 Hashtag</td><td>#心动小镇 · #Heartopia · #HeartopiaGame</td></tr>
    <tr><td>UGC活动</td><td>冰雪季创作计划（2026年1月31日—3月13日）</td></tr>
    <tr><td>国际 TikTok</td><td>尚在起步阶段，主要流量在中文区抖音</td></tr>
  </table>
</div>

<!-- 9. 热门视频 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">9</div>
    <div class="section-title">最火的 5 个视频</div>
  </div>
  <table>
    <tr><th>平台</th><th>创作者</th><th>内容主题</th><th>播放量</th></tr>
    <tr><td>抖音</td><td>官方 @xdxzmobile</td><td>冰雪季更新宣传</td><td>Estimated 百万级</td></tr>
    <tr><td>YouTube</td><td>Psyhodelik</td><td>"Heartopia is The BIGGEST Game of 2026"</td><td>Estimated 万级</td></tr>
    <tr><td>YouTube</td><td>PrettyPoison Gaming</td><td>"10 Advanced Tips That Change Everything"</td><td>Estimated 万级</td></tr>
    <tr><td>YouTube</td><td>Squasha Streams</td><td>"we love heartopia" 直播</td><td><strong>7,000+</strong></td></tr>
    <tr><td>YouTube</td><td>Leo 里歐</td><td>"進入《心動小鎮》和我一起入住！"</td><td>Estimated 3.3万</td></tr>
  </table>
  <div class="card" style="margin-top:14px;">
    <strong>爆火原因：</strong>治愈画面可视化传播强 · 家园展示天然引发"炫耀分享" · 多人直播形成"邀请好友"传播链 · 攻略内容有稳定需求 · VTuber带动二次元社群
  </div>
</div>

<!-- 10. 社区舆情 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">10</div>
    <div class="section-title">社区舆情</div>
  </div>
  <div class="sentiment-block pos">
    <div class="label">✅ 正面评价</div>
    <ul>
      <li>画面治愈、社交互动自由度高，"Animal Crossing + Sims + 多人在线"的独特定位</li>
      <li>内购为装饰性，非 pay-to-win，玩家接受度较高</li>
      <li>TapTap 评分 8.7/10，Steam 上线21天66K同时在线峰值</li>
      <li>IP联动（小马宝莉、喜羊羊）引发破圈效应</li>
    </ul>
  </div>
  <div class="sentiment-block neg">
    <div class="label">❌ 负面评价</div>
    <ul>
      <li>Android 性能问题：部分低端机帧率仅 5-10 FPS</li>
      <li>缺乏 endgame：重复性高，缺乏长期目标</li>
      <li>PC 控制体验差："clunky controls"，感觉是移动端移植版</li>
      <li>Discord 官方服务器管理问题：版主被指控有毒性行为（2026年2月）</li>
    </ul>
  </div>
  <div class="sentiment-block warn">
    <div class="label">⚡️ 争议事件</div>
    <ul>
      <li><strong>种族歧视动画事件（2026年1月）：</strong>黑人角色出现被认为带有歧视意味的动画，引发大量1星差评，版主删评禁言加剧矛盾</li>
      <li><strong>Discord 管理危机（2026年2月）：</strong>官方Discord大规模玩家投诉管理员行为，Reddit 出现 Megathread 专门收集投诉，多个非官方社区分支涌现</li>
    </ul>
  </div>
</div>

<!-- 11. 玩家画像 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">11</div>
    <div class="section-title">核心玩家画像</div>
  </div>
  <table>
    <tr><th>维度</th><th>描述</th></tr>
    <tr><td>年龄层</td><td>主体 16–30岁，青少年和年轻女性为主</td></tr>
    <tr><td>性别</td><td>女性用户偏高（参照同类型 Animal Crossing 用户群）</td></tr>
    <tr><td>核心地区</td><td>🇯🇵 日本（最活跃）· 🇨🇳 中国（核心营销市场）· 🇺🇸 北美（英语内容最多）</td></tr>
    <tr><td>玩家类型</td><td>Casual 为主，部分 Mid-core 创意玩家</td></tr>
    <tr><td>设备偏好</td><td>Mobile 优先，PC 为补充（Steam 整体被评为移动端移植感）</td></tr>
    <tr><td>平均游戏时长</td><td>Estimated 每日 30–60 分钟（日常打卡型）</td></tr>
  </table>
</div>

<!-- 12. 竞品定位 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">12</div>
    <div class="section-title">竞品定位</div>
  </div>
  <table>
    <tr><th>维度</th><th>Heartopia</th><th>Animal Crossing</th><th>The Sims Mobile</th><th>摩尔庄园手游</th></tr>
    <tr>
      <td>多人实时</td>
      <td><span class="badge green">✅ 实时在线</span></td>
      <td><span class="badge red">❌ 无实时</span></td>
      <td><span class="badge red">❌ 无实时</span></td>
      <td><span class="badge green">✅ 支持</span></td>
    </tr>
    <tr>
      <td>商业模式</td>
      <td>F2P + Gacha</td>
      <td>买断制</td>
      <td>F2P + Gacha</td>
      <td>F2P + Gacha</td>
    </tr>
    <tr>
      <td>PC 支持</td>
      <td><span class="badge green">✅ Steam</span></td>
      <td><span class="badge purple">Switch</span></td>
      <td><span class="badge red">❌ 仅 Mobile</span></td>
      <td><span class="badge red">❌ 仅 Mobile</span></td>
    </tr>
    <tr>
      <td>IP 背景</td>
      <td>原创（心动网络）</td>
      <td>任天堂强 IP</td>
      <td>EA 强 IP</td>
      <td>中国老 IP</td>
    </tr>
    <tr>
      <td>核心差异化</td>
      <td><strong>实时多人 + 随机邻里系统</strong></td>
      <td>单机岛屿生活</td>
      <td>剧情驱动</td>
      <td>国内用户为主</td>
    </tr>
  </table>
</div>

<!-- 13. 总结 -->
<div class="section">
  <div class="section-header">
    <div class="section-num">13</div>
    <div class="section-title">总结</div>
  </div>
  <div class="tldr" style="margin-bottom:0;">
    <div class="tldr-title">🔑 五条关键结论</div>
    <ol>
      <li><strong>增长爆发力强，但长期留存存疑</strong> — 上线3天240万下载、21天Steam 66K在线峰值，首发爆发力极强。但"缺乏 endgame"、"重复性高"是核心抱怨，长期月活维持是关键挑战。</li>
      <li><strong>TikTok 营销是核心成功要素</strong> — 161.6万抖音粉丝 + UGC 创作激励活动，是同类手游中罕见的短视频营销成功案例，值得复制和深化。</li>
      <li><strong>社区危机是最大风险点</strong> — 种族歧视动画 + Discord 管理问题叠加，给北美/欧洲市场造成实质性品牌伤害，需要优先处理。</li>
      <li><strong>PC 端是意外惊喜但体验未到位</strong> — Steam 66K 峰值超出预期，但"PC 感觉像移动端移植"是普遍反馈，PC 专项优化将决定能否进一步扩大 PC 玩家群。</li>
      <li><strong>日本市场潜力被严重低估</strong> — App Store 评价数 28,141条（全球最多），评分 4.62（全球最高之一），日本 VTuber 内容产出活跃，是 Heartopia 真正的海外核心市场，值得加大本土化投入。</li>
    </ol>
  </div>
</div>

</div><!-- /container -->

<footer>
  📋 数据说明：标注 "Estimated" 的数据为基于公开信息的合理估算，不代表官方数据。精确数据建议结合 AppMagic / SensorTower 实时校验。<br>
  报告由 小小多 生成 · 2026-03-17
</footer>

</body>
</html>
"""

output_path = REPORT_DIR / "Heartopia_brief_20260317.html"
output_path.write_text(HTML, encoding="utf-8")
print(f"✅ HTML 报告已生成: {output_path}")
print(f"   文件大小: {output_path.stat().st_size / 1024:.1f} KB")
