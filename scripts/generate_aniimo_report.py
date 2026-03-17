#!/usr/bin/env python3
"""Generate Aniimo competitive brief HTML report — standalone, no external deps."""

from pathlib import Path
from datetime import datetime

OUTPUT_PATH = Path(__file__).parent.parent / "reports" / "Aniimo_brief_20260317.html"

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Aniimo 竞品情报简报 2026-03-17</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'PingFang SC','Hiragino Sans GB','Microsoft YaHei',system-ui,sans-serif;background:#07101c;color:#e2eeff;line-height:1.75;min-height:100vh}
body::before{content:'';position:fixed;inset:0;z-index:-1;
  background:radial-gradient(ellipse 70% 55% at 15% 8%,#4f46e520 0,transparent 60%),
             radial-gradient(ellipse 55% 45% at 85% 85%,#7c3aed18 0,transparent 55%),
             radial-gradient(ellipse 45% 38% at 55% 35%,#0ea5e912 0,transparent 50%),
             #07101c}
a{color:#60a5fa;text-decoration:none}a:hover{text-decoration:underline}
/* hero */
.hero{padding:64px 24px 44px;text-align:center;border-bottom:1px solid rgba(99,102,241,.15)}
.hero-badge{display:inline-block;background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3);color:#fbbf24;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:5px 14px;border-radius:100px;margin-bottom:18px}
.hero h1{font-size:clamp(30px,5vw,56px);font-weight:800;background:linear-gradient(135deg,#818cf8 0%,#a78bfa 45%,#38bdf8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}
.hero-meta{color:#64748b;font-size:13px}
/* container */
.wrap{max-width:980px;margin:0 auto;padding:40px 20px 100px}
/* tldr */
.tldr{background:linear-gradient(135deg,rgba(99,102,241,.1) 0%,rgba(124,58,237,.07) 100%);border:1px solid rgba(99,102,241,.25);border-radius:16px;padding:28px 32px;margin-bottom:44px}
.tldr-label{font-size:11px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#818cf8;margin-bottom:18px}
.tldr ol{padding-left:20px}.tldr li{margin-bottom:12px;font-size:15px}.tldr li strong{color:#a5b4fc}
/* section */
.sec{margin-bottom:52px}
.sec-head{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid rgba(99,102,241,.1)}
.sec-num{width:30px;height:30px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff;flex-shrink:0}
.sec-title{font-size:19px;font-weight:700;color:#e2eeff}
/* table */
.tbl-wrap{overflow-x:auto;border-radius:12px;border:1px solid rgba(99,102,241,.12)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{background:rgba(99,102,241,.09);color:#a5b4fc;font-weight:600;font-size:11px;letter-spacing:.8px;text-transform:uppercase;padding:11px 14px;text-align:left;border-bottom:1px solid rgba(99,102,241,.12)}
td{padding:12px 14px;border-bottom:1px solid rgba(255,255,255,.04);color:#e2eeff;vertical-align:top}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(99,102,241,.04)}
/* cards */
.card{background:rgba(255,255,255,.035);border:1px solid rgba(99,102,241,.1);border-radius:12px;padding:20px 24px;margin-bottom:14px}
.note{background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.22);border-radius:8px;padding:11px 16px;font-size:13px;color:#fbbf24;margin-bottom:14px}
.note-blue{background:rgba(96,165,250,.07);border:1px solid rgba(96,165,250,.18);border-radius:8px;padding:11px 16px;font-size:13px;color:#93c5fd;margin-bottom:14px}
.note-red{background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.2);border-radius:8px;padding:10px 16px;font-size:13px;color:#fca5a5;margin-top:12px}
/* sentiment grid */
.sentiment-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:640px){.sentiment-grid{grid-template-columns:1fr}}
.s-pos{background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.2);border-radius:10px;padding:16px}
.s-neg{background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.2);border-radius:10px;padding:16px}
.s-pos-title{color:#34d399;font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:10px}
.s-neg-title{color:#f87171;font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:10px}
.s-pos ul,.s-neg ul{padding-left:16px;font-size:14px;line-height:1.8}
.s-warn{background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.2);border-radius:10px;padding:16px}
.s-warn-title{color:#fbbf24;font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:8px}
/* summary cards */
.sum-card{border-left:3px solid;border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:12px}
.sum-card p{font-size:14px;color:#94a3b8;margin-top:5px}
/* hot badge */
.hot{color:#f87171;font-weight:700}
.green{color:#34d399}.blue{color:#60a5fa}.yellow{color:#fbbf24}.purple{color:#a78bfa}.gray{color:#64748b}
/* footer */
.footer{margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,.06);font-size:12px;color:#475569}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-badge">⚠️ 上线前 · Pre-Launch</div>
  <h1>Aniimo 竞品情报简报</h1>
  <p class="hero-meta">报告日期：2026-03-17 &nbsp;|&nbsp; 开发商：Pawprint Studio &nbsp;|&nbsp; 发行商：Kingsglory (FunPlus) &nbsp;|&nbsp; 数据来源：SteamDB · IGN · PC Gamer · Reddit · YouTube</p>
</div>

<div class="wrap">

<!-- TL;DR -->
<div class="tldr">
  <div class="tldr-label">⚡ 关键结论 TL;DR</div>
  <ol>
    <li><strong>YouTube官方频道310万订阅</strong>极其罕见 — 游戏尚未发售已有如此体量，FunPlus/Kingsglory重资源投入，首发表现压力极大</li>
    <li><strong>Gacha是最大定时炸弹</strong> — IGN、PC Gamer、Reddit Beta玩家均将Gacha列为核心担忧；PC/Xbox玩家对Gacha接受度远低于移动端</li>
    <li><strong>"缺乏原创性"是最危险的评价</strong> — PC Gamer直说"所有东西都被别人做得更好"，正式发布前必须建立清晰独特身份</li>
    <li><strong>Steam Wishlist #149 全球排名</strong> + 23,823 Followers — 预热数据亮眼，但Beta高端PC FPS下降问题若不解决，Steam首日评价将崩塌</li>
    <li><strong>Xbox平台是真正差异化机会</strong> — Xbox上几乎无同类竞品，可避开与Pokémon/Genshin的正面竞争</li>
  </ol>
</div>

<!-- 1. 基础信息 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">1</div><h2 class="sec-title">游戏基础信息</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>字段</th><th>内容</th></tr>
    <tr><td>游戏名称</td><td><strong>Aniimo</strong></td></tr>
    <tr><td>开发商</td><td>Pawprint Studio</td></tr>
    <tr><td>发行商</td><td>Kingsglory（FunPlus 旗下新发行品牌）</td></tr>
    <tr><td>预计发布</td><td>2026年（具体日期未定）</td></tr>
    <tr><td>游戏类型</td><td>精灵捕捉 · 开放世界动作 RPG（Creature-catching Open World ARPG）</td></tr>
    <tr><td>商业模式</td><td>Free-to-Play + Gacha</td></tr>
    <tr><td>支持平台</td><td>PC（Steam / Microsoft Store）· Xbox Series X|S · iOS · Android</td></tr>
    <tr><td>技术亮点</td><td>Nvidia DLSS 4.5 支持（2026年3月官宣）</td></tr>
    <tr><td>官方网站</td><td><a href="https://www.aniimo.com/" target="_blank">aniimo.com</a> · <a href="https://funplus.com/games/aniimo/" target="_blank">FunPlus页面</a></td></tr>
  </table></div>
</div>

<!-- 2. 下载量 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">2</div><h2 class="sec-title">下载量与平台分布</h2></div>
  <div class="note">⚠️ 游戏尚未正式发布，以下为预发布阶段数据</div>
  <div class="tbl-wrap"><table>
    <tr><th>平台</th><th>指标</th><th>数据</th></tr>
    <tr><td rowspan="3"><strong>PC (Steam)</strong></td><td>状态</td><td>Coming Soon（Wishlist 开放中）</td></tr>
    <tr><td>全球 Wishlist 排名</td><td><strong class="blue">#149</strong>（SteamDB 实际数据）</td></tr>
    <tr><td>Steam Followers</td><td><strong class="blue">23,823</strong>（SteamDB 实际数据）</td></tr>
    <tr><td><strong>Xbox</strong></td><td>状态</td><td>预约页已上架 · Xbox Play Anywhere 支持</td></tr>
    <tr><td rowspan="2"><strong>Mobile</strong></td><td>iOS</td><td>预注册中 · 2025年12月完成移动端技术测试</td></tr>
    <tr><td>Android</td><td>预注册中</td></tr>
  </table></div>
  <p style="margin-top:12px;font-size:13px;color:#64748b">
    🔗 <a href="https://store.steampowered.com/app/4126040/Aniimo/" target="_blank">Steam商店</a> ·
    <a href="https://steamdb.info/app/4126040/" target="_blank">SteamDB</a> ·
    <a href="https://www.xbox.com/en-US/games/store/aniimo/9pk8phlcqdf6" target="_blank">Xbox Store</a>
  </p>
</div>

<!-- 3. 地区分布 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">3</div><h2 class="sec-title">地区用户分布</h2></div>
  <div class="note-blue">估算依据：Steam语言支持分布 · Beta测试区域 · 媒体报道来源 · Xbox平台推广重心</div>
  <div class="tbl-wrap"><table>
    <tr><th>地区</th><th>预期热度</th><th>代理指标</th><th>信心</th></tr>
    <tr><td>🇺🇸 北美</td><td><strong class="green">高</strong></td><td>Xbox平台核心推广区 · 英语媒体覆盖最多</td><td>★★★★☆</td></tr>
    <tr><td>🇪🇺 欧洲</td><td><strong class="blue">中-高</strong></td><td>PC Gamer/GAMINGbible报道 · 多欧语支持</td><td>★★★☆☆</td></tr>
    <tr><td>🇯🇵 日本</td><td><strong class="blue">中</strong></td><td>TGS 2025参展 · 日语支持 · 精灵捕捉成熟市场</td><td>★★★☆☆</td></tr>
    <tr><td>🇰🇷 韩国</td><td><strong class="gray">中</strong></td><td>韩语支持 · FunPlus亚洲发行基础</td><td>★★☆☆☆</td></tr>
    <tr><td>🇸🇬🇮🇩 东南亚</td><td><strong class="blue">中</strong></td><td>泰/印尼/越南语支持 · F2P Gacha高接受度</td><td>★★★☆☆</td></tr>
    <tr><td>🇧🇷 拉美</td><td><strong class="gray">中</strong></td><td>巴西葡语 + 拉丁美洲西班牙语支持</td><td>★★☆☆☆</td></tr>
  </table></div>
</div>

<!-- 4. 社媒账号 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">4</div><h2 class="sec-title">官方社媒账号</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>平台</th><th>账号</th><th>粉丝数</th></tr>
    <tr><td>📺 YouTube</td><td><a href="https://www.youtube.com/@Aniimo" target="_blank">@Aniimo</a></td><td><strong class="hot">310万订阅 🔥</strong></td></tr>
    <tr><td>🐦 Twitter / X</td><td><a href="https://twitter.com/Aniimo_EN" target="_blank">@Aniimo_EN</a></td><td class="gray">Estimated 数万</td></tr>
    <tr><td>🎵 TikTok</td><td><a href="https://www.tiktok.com/@aniimo_na" target="_blank">@aniimo_na</a></td><td class="gray">Estimated 数万</td></tr>
    <tr><td>💬 Discord</td><td><a href="https://discord.com/invite/aniimo" target="_blank">discord.com/invite/aniimo</a></td><td>活跃社区</td></tr>
    <tr><td>📱 Reddit</td><td><a href="https://www.reddit.com/r/Aniimo/" target="_blank">r/Aniimo</a></td><td>Beta讨论活跃</td></tr>
  </table></div>
  <div class="note-red">📌 YouTube 310万订阅是极其罕见的预发布数字，远超同期绝大多数未发售游戏</div>
</div>

<!-- 5. 媒体报道 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">5</div><h2 class="sec-title">媒体报道</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>媒体</th><th>时间</th><th>标题摘要</th><th>倾向</th></tr>
    <tr><td><a href="https://sea.ign.com/aniimo/238083/preview/aniimo-preview-all-the-fun-of-creature-catching-with-all-the-transactions-of-gacha" target="_blank">IGN</a></td><td>2026-01-30</td><td>"All the Fun of Creature-Catching with All the Transactions of Gacha"</td><td><span class="yellow">⚠️ 中性偏负</span></td></tr>
    <tr><td><a href="https://www.pcgamer.com/games/rpg/a-pokemon-like-gacha-game-should-be-such-an-obvious-win-that-im-shocked-i-cant-find-much-to-like-about-aniimo/" target="_blank">PC Gamer</a></td><td>2026-01-29</td><td>"Should be an obvious win... I can't find much to like"</td><td><span style="color:#f87171">❌ 负面</span></td></tr>
    <tr><td><a href="https://www.gamingbible.com/news/platform/xbox/xbox-2026-exclusive-352075-20251216" target="_blank">GAMINGbible</a></td><td>2025-12</td><td>"Xbox's Answer to Pokémon"</td><td><span class="green">✅ 正面</span></td></tr>
    <tr><td><a href="https://news.seagm.com/aniimo-breakdown-why-this-free-arpg-might-outshine-palworld-in-2026/" target="_blank">SEAGM News</a></td><td>2025-06</td><td>"Why this free ARPG might outshine Palworld in 2026"</td><td><span class="green">✅ 正面</span></td></tr>
    <tr><td><a href="https://www.gamespot.com/articles/pokemon-like-game-aniimo-announced-for-xbox-and-pc/1100-6532230/" target="_blank">GameSpot</a></td><td>2025</td><td>"Pokémon-like game announced for Xbox and PC"</td><td><span class="blue">ℹ️ 中性</span></td></tr>
    <tr><td><a href="https://www.gematsu.com/2025/09/aniimo-tgs-2025-trailer-screenshots" target="_blank">Gematsu</a></td><td>TGS 2025</td><td>TGS Trailer + Screenshots</td><td><span class="blue">ℹ️ 中性</span></td></tr>
  </table></div>
</div>

<!-- 6. LiveOps -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">6</div><h2 class="sec-title">最近3个月 LiveOps 动态</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>时间</th><th>内容</th></tr>
    <tr><td>2025-12</td><td>iOS 移动端技术测试（Mobile Technical Test）</td></tr>
    <tr><td>2026-01-23</td><td>"Paws Up" 第二次全球封闭Beta开启 — 新Aniimo生物 · 新Boss · Twining机制 · Homeland家园建造</td></tr>
    <tr><td>2026-02-08</td><td>第二次Beta结束，官方收集玩家反馈</td></tr>
    <tr><td>2026-03-12</td><td>官宣 Nvidia DLSS 4.5 支持，发布官方 DLSS Trailer</td></tr>
    <tr><td>2026-03（近期）</td><td>"A New World of Adventure" 新预告 + Pre-Register Now 活动</td></tr>
  </table></div>
  <p style="margin-top:10px;font-size:13px;color:#64748b">🔗 <a href="https://www.aniimo.com/newslist/detail/gljrwyl5" target="_blank">官方新闻页</a></p>
</div>

<!-- 7. YouTube生态 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">7</div><h2 class="sec-title">YouTube 创作者生态</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>创作者</th><th>粉丝数</th><th>代表内容</th><th>播放量</th></tr>
    <tr><td><strong>Aniimo 官方</strong></td><td class="hot">310万</td><td>官方预告、DLSS Trailer</td><td>—</td></tr>
    <tr><td>The AxeMan</td><td>—</td><td>"This NEW Open World Creature Capture Game Is INSANE !!"</td><td><strong class="blue">404K</strong></td></tr>
    <tr><td><a href="https://www.youtube.com/watch?v=r9_pS1vJbvI" target="_blank">Cjthecheesedj</a></td><td>241K</td><td>"I Spent 100 Days In ANIIMO!!"</td><td>112K</td></tr>
    <tr><td>MunchingOrange</td><td>1.38M</td><td>Pokémon社区代表，Aniimo内容</td><td>—</td></tr>
    <tr><td>Purplecliffe</td><td>1.4M</td><td>Pokémon社区代表，Aniimo内容</td><td>—</td></tr>
    <tr><td>RvNx Mango</td><td>449K</td><td>Beta实机内容</td><td>—</td></tr>
    <tr><td>United Plays</td><td>636K</td><td>Beta内容</td><td>—</td></tr>
    <tr><td>TagBackTV</td><td>—</td><td>"Aniimo IS EASILY The Best Creature Catching Game"</td><td>9K</td></tr>
  </table></div>
  <p style="margin-top:10px;font-size:13px;color:#64748b">📌 官方 Content Creator Program 已启动，Beta期间组织创作者参与测试</p>
</div>

<!-- 8. TikTok -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">8</div><h2 class="sec-title">TikTok 内容生态</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>指标</th><th>数据</th></tr>
    <tr><td>官方账号</td><td><a href="https://www.tiktok.com/@aniimo_na" target="_blank">@aniimo_na</a></td></tr>
    <tr><td>粉丝数</td><td class="gray">Estimated 数万（游戏未发布，体量有限）</td></tr>
    <tr><td>主要 Hashtag</td><td>#Aniimo · #AniimoGame · #CreatureCatching</td></tr>
    <tr><td>内容类型</td><td>精灵展示、Twining演示、开放世界探索片段</td></tr>
    <tr><td>整体评估</td><td>TikTok生态处于起步阶段，YouTube是当前主要内容平台</td></tr>
  </table></div>
</div>

<!-- 9. 最火视频 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">9</div><h2 class="sec-title">最火 5 个视频</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>#</th><th>创作者</th><th>视频标题</th><th>播放量</th><th>链接</th></tr>
    <tr><td>1</td><td>The AxeMan</td><td>"This NEW Open World Creature Capture Game Is INSANE !!"</td><td><strong class="blue">404K</strong></td><td><a href="https://www.youtube.com/watch?v=y8hv8DotbX0" target="_blank">▶</a></td></tr>
    <tr><td>2</td><td>Cjthecheesedj</td><td>"I Spent 100 Days In ANIIMO!! Here's What Happened...."</td><td>112K</td><td><a href="https://www.youtube.com/watch?v=r9_pS1vJbvI" target="_blank">▶</a></td></tr>
    <tr><td>3</td><td>Aniimo官方</td><td>Official DLSS 4.5 Trailer</td><td class="gray">Estimated 数十万</td><td><a href="https://www.youtube.com/watch?v=dbcABWrOHUQ" target="_blank">▶</a></td></tr>
    <tr><td>4</td><td>TagBackTV</td><td>"Aniimo IS EASILY The Best Creature Catching Open World RPG"</td><td>9K</td><td><a href="https://www.youtube.com/watch?v=fjSZIipVkhA" target="_blank">▶</a></td></tr>
    <tr><td>5</td><td>Verlisify</td><td>"ANIIMO IS THE BEST CREATURE CATCHING GAME EVER MADE! Beta 2 Review"</td><td>4.7K</td><td>YouTube</td></tr>
  </table></div>
</div>

<!-- 10. 社区舆情 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">10</div><h2 class="sec-title">社区舆情</h2></div>
  <div class="sentiment-grid">
    <div class="s-pos">
      <div class="s-pos-title">✅ 正面评价</div>
      <ul>
        <li><strong>画面与美术</strong>：视觉效果"精美"，Aniimo生物设计有特色</li>
        <li><strong>角色创建</strong>："非常深度"，自定义空间大（IGN重点表扬）</li>
        <li><strong>Twining机制</strong>：变身精灵战斗/移动，被广泛认为是真正创新</li>
        <li><strong>战斗流畅感</strong>：Beta阶段已"流畅且执行到位"</li>
        <li><strong>4人合作</strong>：PvE + PvP + 交易，社交维度丰富</li>
      </ul>
    </div>
    <div class="s-neg">
      <div class="s-neg-title">❌ 负面评价</div>
      <ul>
        <li><strong>Gacha担忧（核心）</strong>：IGN标题直接写出，Reddit持续发酵</li>
        <li><strong>缺乏原创性</strong>：PC Gamer："所有东西都被别人做得更好"</li>
        <li><strong>Beta技术问题</strong>：高端PC FPS下降 · 视觉Bug · 缺基础设置</li>
        <li><strong>语音质量</strong>：部分VO被描述为"没有生气"，接近TTS</li>
        <li><strong>教程不清晰</strong>：新手引导不到位</li>
      </ul>
    </div>
  </div>
  <div class="s-warn">
    <div class="s-warn-title">⚡️ 核心争议</div>
    <p style="font-size:14px;line-height:1.8">
      1. <strong>Gacha vs 精灵捕捉</strong>：社区核心争论——"Palworld没有Gacha所以成功，Aniimo加了Gacha是自杀还是必要？"<br>
      2. <strong>原创性争议</strong>：被同时批评"太像Pokémon"和"太像Palworld"，尚未建立独特身份<br>
      3. <strong>"Pokémon Killer"标签</strong>：预期管理风险极高——贴上这个标签的游戏几乎都失败了
    </p>
  </div>
</div>

<!-- 11. 玩家画像 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">11</div><h2 class="sec-title">核心玩家画像</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>维度</th><th>描述</th></tr>
    <tr><td>年龄层</td><td>主体 16-30岁；Pokémon核心受众（80、90后）+ 年轻新玩家</td></tr>
    <tr><td>性别</td><td>混合，精灵捕捉类型女性用户占比较高</td></tr>
    <tr><td>核心地区</td><td>北美（Xbox/PC）· 欧洲（PC）· 东南亚（移动端F2P）</td></tr>
    <tr><td>玩家类型</td><td>精灵收集核心玩家 + 开放世界ARPG玩家 + Palworld流失玩家</td></tr>
    <tr><td>设备偏好</td><td>PC/Xbox为主（发布初期），移动端为长期增量</td></tr>
    <tr><td>竞品参照</td><td>Pokémon（IP情怀）· Palworld（近期对标）· Genshin Impact（商业化参照）</td></tr>
  </table></div>
</div>

<!-- 12. 竞品定位 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">12</div><h2 class="sec-title">竞品定位</h2></div>
  <div class="tbl-wrap"><table>
    <tr><th>维度</th><th>Aniimo</th><th>Palworld</th><th>Pokémon（正传）</th><th>Genshin Impact</th></tr>
    <tr><td><strong>平台</strong></td><td>PC/Xbox/Mobile</td><td>PC/Xbox/Mobile</td><td>Switch/Mobile</td><td>PC/Mobile/PS</td></tr>
    <tr><td><strong>商业模式</strong></td><td>F2P + Gacha</td><td>买断制</td><td>买断制</td><td>F2P + Gacha</td></tr>
    <tr><td><strong>精灵收集</strong></td><td class="green">✅ 核心</td><td class="green">✅ 核心</td><td class="green">✅ IP根基</td><td style="color:#f87171">❌ 角色收集</td></tr>
    <tr><td><strong>开放世界</strong></td><td class="green">✅ 大世界</td><td class="green">✅ 大世界</td><td class="green">✅ 近年加入</td><td class="green">✅ 大世界</td></tr>
    <tr><td><strong>多人合作</strong></td><td class="green">✅ 4人</td><td class="green">✅ 4人</td><td class="yellow">⚠️ 有限</td><td class="yellow">⚠️ 有限</td></tr>
    <tr><td><strong>IP认知</strong></td><td style="color:#f87171">❌ 新IP</td><td style="color:#f87171">❌ 新IP</td><td class="green">✅ 全球最强</td><td class="green">✅ 全球知名</td></tr>
    <tr><td><strong>主机支持</strong></td><td class="green">✅ Xbox</td><td class="green">✅ Xbox</td><td class="green">✅ Switch</td><td class="yellow">⚠️ 仅PS</td></tr>
    <tr><td><strong>Gacha争议</strong></td><td style="color:#f87171">⚠️ 高风险</td><td class="green">✅ 无Gacha</td><td class="green">✅ 无Gacha</td><td class="green">✅ 已被接受</td></tr>
  </table></div>
</div>

<!-- 13. 总结 -->
<div class="sec">
  <div class="sec-head"><div class="sec-num">13</div><h2 class="sec-title">总结</h2></div>
  <div class="sum-card" style="background:rgba(96,165,250,.07);border-color:#60a5fa">
    <strong class="blue">① 310万YouTube订阅 = FunPlus的豪赌</strong>
    <p>Kingsglory作为FunPlus新发行品牌首款游戏，发布结果将直接影响该品牌未来，高期待值是双刃剑。</p>
  </div>
  <div class="sum-card" style="background:rgba(248,113,113,.07);border-color:#f87171">
    <strong style="color:#f87171">② Gacha定价策略是决定命运的关键决策</strong>
    <p>PC/Xbox玩家Gacha接受度极低。发布前必须清晰传达"Gacha不影响核心游玩"，否则Steam首日评价将崩塌。</p>
  </div>
  <div class="sum-card" style="background:rgba(251,191,36,.07);border-color:#fbbf24">
    <strong class="yellow">③ Beta技术问题必须发布前解决</strong>
    <p>高端PC FPS下降、视觉Bug、缺基础设置——这些在Steam首日会被放大百倍，48小时内评价将定型。</p>
  </div>
  <div class="sum-card" style="background:rgba(167,139,250,.07);border-color:#a78bfa">
    <strong class="purple">④ 放弃"Pokémon Killer"标签，建立独特身份</strong>
    <p>贴上这个标签的游戏几乎都失败了。Aniimo需要自己的叙事：不是"下一个Pokémon"，而是"第一个真正意义上的开放世界多人精灵ARPG"。</p>
  </div>
  <div class="sum-card" style="background:rgba(52,211,153,.07);border-color:#34d399">
    <strong class="green">⑤ Xbox平台是真正的差异化机会</strong>
    <p>Xbox上几乎无同类竞品，优先打透Xbox核心用户群可避开与Pokémon/Genshin的正面竞争，再渗透PC和移动端。</p>
  </div>
  <div class="footer">数据说明：游戏尚未正式发布。SteamDB Wishlist #149、Followers 23,823 为实际数据，其余标注 Estimated。建议发布后用 SensorTower / AppMagic / SteamDB 实时更新。</div>
</div>

</div>
</body>
</html>"""


def main():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(HTML, encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"✅ HTML report generated: {OUTPUT_PATH}")
    print(f"   Size: {size_kb:.1f} KB")
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    main()
