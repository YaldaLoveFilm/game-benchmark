#!/usr/bin/env python3
"""
HTML Report Generator — converts benchmark results to a styled, clickable report.
Design: Space Grotesk + Plus Jakarta Sans, grain texture, glassmorphism, mesh gradients,
scroll-triggered animations. Style adapts to game genre automatically.
"""
import json, os, re
from pathlib import Path
from datetime import datetime

THEMES = {
    "cozy": {
        "bg_from":"#1a0a1e","bg_to":"#2d1040",
        "mesh1":"#ff6b9d44","mesh2":"#c084fc33","mesh3":"#fb923c22",
        "primary":"#ff6b9d","secondary":"#c084fc","accent":"#fb923c",
        "text":"#fdf4ff","subtext":"#d8b4fe","border":"rgba(255,107,157,0.2)",
        "card_bg":"rgba(255,255,255,0.05)","card_border":"rgba(255,107,157,0.15)",
        "badge_bg":"rgba(255,107,157,0.10)","glow":"rgba(255,107,157,0.3)",
        "header_grad":"linear-gradient(135deg,#ff6b9d 0%,#c084fc 60%,#fb923c 100%)",
        "emoji":"🌸",
    },
    "action": {
        "bg_from":"#080b12","bg_to":"#0f1520",
        "mesh1":"#ff444444","mesh2":"#ff8c0033","mesh3":"#ffd70011",
        "primary":"#ff4444","secondary":"#ff8c00","accent":"#ffd700",
        "text":"#f5f5f5","subtext":"#9ca3af","border":"rgba(255,68,68,0.2)",
        "card_bg":"rgba(255,255,255,0.04)","card_border":"rgba(255,68,68,0.15)",
        "badge_bg":"rgba(255,68,68,0.10)","glow":"rgba(255,68,68,0.4)",
        "header_grad":"linear-gradient(135deg,#ff4444 0%,#ff8c00 60%,#ffd700 100%)",
        "emoji":"⚔️",
    },
    "strategy": {
        "bg_from":"#080f1a","bg_to":"#0d1829",
        "mesh1":"#3b82f644","mesh2":"#8b5cf633","mesh3":"#06b6d422",
        "primary":"#60a5fa","secondary":"#a78bfa","accent":"#34d399",
        "text":"#f0f9ff","subtext":"#94a3b8","border":"rgba(96,165,250,0.2)",
        "card_bg":"rgba(255,255,255,0.04)","card_border":"rgba(96,165,250,0.15)",
        "badge_bg":"rgba(96,165,250,0.10)","glow":"rgba(96,165,250,0.3)",
        "header_grad":"linear-gradient(135deg,#3b82f6 0%,#8b5cf6 60%,#06b6d4 100%)",
        "emoji":"🏰",
    },
    "simulation": {
        "bg_from":"#061210","bg_to":"#0a1f1c",
        "mesh1":"#22c55e44","mesh2":"#06b6d433","mesh3":"#f59e0b22",
        "primary":"#4ade80","secondary":"#22d3ee","accent":"#fbbf24",
        "text":"#f0fdf4","subtext":"#86efac","border":"rgba(74,222,128,0.2)",
        "card_bg":"rgba(255,255,255,0.04)","card_border":"rgba(74,222,128,0.15)",
        "badge_bg":"rgba(74,222,128,0.08)","glow":"rgba(74,222,128,0.3)",
        "header_grad":"linear-gradient(135deg,#22c55e 0%,#06b6d4 60%,#f59e0b 100%)",
        "emoji":"🏡",
    },
    "rpg": {
        "bg_from":"#0d0815","bg_to":"#1a0d2e",
        "mesh1":"#a855f744","mesh2":"#ec489933","mesh3":"#f59e0b22",
        "primary":"#c084fc","secondary":"#f472b6","accent":"#fbbf24",
        "text":"#faf5ff","subtext":"#c4b5fd","border":"rgba(192,132,252,0.2)",
        "card_bg":"rgba(255,255,255,0.04)","card_border":"rgba(192,132,252,0.15)",
        "badge_bg":"rgba(192,132,252,0.10)","glow":"rgba(192,132,252,0.4)",
        "header_grad":"linear-gradient(135deg,#a855f7 0%,#ec4899 60%,#f59e0b 100%)",
        "emoji":"🧙",
    },
    "default": {
        "bg_from":"#09090b","bg_to":"#18181b",
        "mesh1":"#6366f144","mesh2":"#8b5cf633","mesh3":"#06b6d422",
        "primary":"#818cf8","secondary":"#a78bfa","accent":"#22d3ee",
        "text":"#fafafa","subtext":"#a1a1aa","border":"rgba(129,140,248,0.2)",
        "card_bg":"rgba(255,255,255,0.04)","card_border":"rgba(129,140,248,0.15)",
        "badge_bg":"rgba(129,140,248,0.10)","glow":"rgba(129,140,248,0.3)",
        "header_grad":"linear-gradient(135deg,#6366f1 0%,#8b5cf6 60%,#06b6d4 100%)",
        "emoji":"🎮",
    },
}

GENRE_THEME_MAP = {
    "simulation":"simulation","casual":"cozy","social":"cozy","lifestyle":"cozy",
    "entertainment":"cozy","family":"cozy","action":"action","shooting":"action",
    "adventure":"action","strategy":"strategy","puzzle":"strategy","board":"strategy",
    "role":"rpg","rpg":"rpg","fantasy":"rpg","sports":"default","racing":"action","music":"cozy",
}

def detect_theme(results):
    for g in (results.get("appstore",{}).get("genres",[]) or []):
        for key, theme in GENRE_THEME_MAP.items():
            if key in g.lower(): return theme
    genre = (results.get("googleplay",{}).get("genre") or "").lower()
    for key, theme in GENRE_THEME_MAP.items():
        if key in genre: return theme
    return "default"

def fmt(n):
    if n is None: return "N/A"
    try: n = int(n)
    except: return str(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)

def e(s): # html escape
    if not s: return ""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')

def load_css():
    css_path = Path(__file__).parent / "_report_styles.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""

def generate_html(game_name, results, output_path=None):
    t = THEMES[detect_theme(results)]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    css = load_css()

    # Inject theme CSS variables
    theme_vars = f"""
    :root {{
        --primary:{t['primary']};--secondary:{t['secondary']};--accent:{t['accent']};
        --text:{t['text']};--subtext:{t['subtext']};--border:{t['border']};
        --card-bg:{t['card_bg']};--card-border:{t['card_border']};
        --badge-bg:{t['badge_bg']};--glow:{t['glow']};
        --header-grad:{t['header_grad']};
        --bg-from:{t['bg_from']};--bg-to:{t['bg_to']};
        --mesh1:{t['mesh1']};--mesh2:{t['mesh2']};--mesh3:{t['mesh3']};
    }}"""

    secs = []

    # ── Platform Coverage ──────────────────────────────────────────
    plats = []
    if results.get("steam") and "error" not in results.get("steam",{}): plats.append("🖥️ PC (Steam)")
    if results.get("appstore") and "error" not in results.get("appstore",{}): plats.append("🍎 iOS")
    gp = results.get("googleplay",{})
    if gp and gp.get("name") and "error" not in gp: plats.append("🤖 Android")
    if results.get("taptap",{}).get("name"): plats.append("🟢 TapTap")
    if plats:
        tags = "".join(f'<span class="platform-tag">{p}</span>' for p in plats)
        secs.append(f'<div class="card reveal"><div class="card-label">🖥️ Platform Coverage</div><div class="platform-tags">{tags}</div></div>')

    # ── Stores (App Store + Google Play) ──────────────────────────
    store_html = ""
    appstore = results.get("appstore",{})
    if appstore and "error" not in appstore:
        rating = appstore.get("rating") or 0
        pct = min(100, int(rating/5.0*100))
        rev = appstore.get("review_summary",{})
        pos = "".join(f'<div class="review-pill pos">✅ {e(s[:90])}</div>' for s in rev.get("positive_snippets",[])[:1])
        neg = "".join(f'<div class="review-pill neg">❌ {e(s[:90])}</div>' for s in rev.get("negative_snippets",[])[:2])
        lnk = f'<a href="{e(appstore.get("url",""))}" target="_blank" class="store-link">View on App Store ↗</a>' if appstore.get("url") else ""
        store_html += f"""<div class="store-card">
            <div class="store-header">🍎 App Store</div>
            <div class="store-name">{e(appstore.get("name",""))}</div>
            <div class="rating-row">
                <div class="rating-num">{rating:.1f}</div>
                <div class="rating-bar-wrap"><div class="rating-bar" data-width="{pct}" style="width:0"></div></div>
                <div class="rating-sub">{fmt(appstore.get("rating_count"))} reviews</div>
            </div>
            <div class="store-meta">{e(appstore.get("developer",""))} · {e(appstore.get("price","Free"))} · v{e(appstore.get("version",""))}</div>
            {pos}{neg}{lnk}</div>"""

    if gp and gp.get("name") and "error" not in gp:
        rating = gp.get("rating") or 0
        pct = min(100, int(rating/5.0*100))
        ri = gp.get("real_installs")
        installs = f"{ri:,}" if ri else gp.get("installs","—")
        rev = gp.get("review_summary",{})
        pos = "".join(f'<div class="review-pill pos">✅ {e(s[:90])}</div>' for s in rev.get("positive_snippets",[])[:1])
        neg = "".join(f'<div class="review-pill neg">❌ {e(s[:90])}</div>' for s in rev.get("negative_snippets",[])[:2])
        lnk = f'<a href="{e(gp.get("url",""))}" target="_blank" class="store-link">View on Google Play ↗</a>' if gp.get("url") else ""
        store_html += f"""<div class="store-card">
            <div class="store-header">🤖 Google Play</div>
            <div class="store-name">{e(gp.get("name",""))}</div>
            <div class="rating-row">
                <div class="rating-num">{rating:.1f}</div>
                <div class="rating-bar-wrap"><div class="rating-bar" data-width="{pct}" style="width:0"></div></div>
                <div class="rating-sub">{fmt(gp.get("rating_count"))} ratings</div>
            </div>
            <div class="store-meta">{e(gp.get("developer",""))} · {installs} installs</div>
            {pos}{neg}{lnk}</div>"""

    if store_html:
        secs.append(f'<div class="card reveal store-grid">{store_html}</div>')

    # ── Official Accounts ──────────────────────────────────────────
    social = results.get("social_accounts",{})
    if social:
        ICONS  = {"youtube":"▶️","twitter_x":"🐦","facebook":"📘","tiktok":"🎵","instagram":"📷","reddit":"🔴","discord":"💬"}
        LABELS = {"youtube":"YouTube","twitter_x":"X / Twitter","facebook":"Facebook","tiktok":"TikTok","instagram":"Instagram","reddit":"Reddit","discord":"Discord"}
        rows = ""
        for plat, info in social.items():
            url = info.get("url") or ""
            if not url: continue
            label = LABELS.get(plat, plat)
            icon  = ICONS.get(plat,"🔗")
            subs  = info.get("subscribers") or info.get("followers") or info.get("members")
            extra = f'<span class="social-count">{fmt(subs)}</span>' if subs else ""
            if plat == "youtube":
                extra = f'<span class="social-count">{fmt(info.get("subscribers"))} subs · {fmt(info.get("video_count"))} videos</span>'
            rows += f'<a href="{e(url)}" target="_blank" rel="noopener" class="social-row"><span class="social-icon">{icon}</span><span class="social-label">{label}</span>{extra}<span class="social-arrow">↗</span></a>'
        secs.append(f'<div class="card reveal"><div class="card-label">🏢 Official Accounts</div><div class="social-list">{rows}</div></div>')

    # ── Top Videos ────────────────────────────────────────────────
    vids = (results.get("top_videos") or {}).get("videos",[])
    if vids:
        items = ""
        for i,v in enumerate(vids[:5],1):
            items += f"""<a href="{e(v['url'])}" target="_blank" rel="noopener" class="video-item">
                <div class="video-rank-badge">#{i}</div>
                <img class="video-thumb" src="https://img.youtube.com/vi/{e(v['video_id'])}/mqdefault.jpg" alt="" loading="lazy">
                <div class="video-info">
                    <div class="video-title">{e(v['title'][:68])}</div>
                    <div class="video-stats">
                        <span>👁 {fmt(v['views'])}</span><span>👍 {fmt(v['likes'])}</span>
                        <span>📅 {e(v['published_at'])}</span>
                        <span class="video-channel">📺 {e(v['channel'][:22])}</span>
                    </div>
                </div></a>"""
        secs.append(f'<div class="card reveal full-width"><div class="card-label">🏆 Top Videos — Last 90 Days</div><div class="video-list">{items}</div></div>')

    # ── Creator Ecosystem ──────────────────────────────────────────
    eco = results.get("creator_ecosystem",{})
    creators = eco.get("top_creators",[])
    if creators:
        total = eco.get("video_count_estimate",0)
        mega  = [c for c in creators if c["subscribers"] and c["subscribers"]>=1_000_000]
        macro = [c for c in creators if c["subscribers"] and 100_000<=c["subscribers"]<1_000_000]
        mid   = [c for c in creators if c["subscribers"] and 10_000<=c["subscribers"]<100_000]
        micro = [c for c in creators if c["subscribers"] and c["subscribers"]<10_000]
        pills = ""
        if mega:  pills += f'<div class="tier-pill mega">🏆 Mega 1M+ <strong>{len(mega)}</strong></div>'
        if macro: pills += f'<div class="tier-pill macro">⭐ Macro 100K <strong>{len(macro)}</strong></div>'
        if mid:   pills += f'<div class="tier-pill mid">📈 Mid 10K <strong>{len(mid)}</strong></div>'
        if micro: pills += f'<div class="tier-pill micro">🌱 Micro &lt;10K <strong>{len(micro)}</strong></div>'
        rows = ""
        for i,c in enumerate(creators[:20],1):
            subs = fmt(c["subscribers"]) if c["subscribers"] else "—"
            link = c.get("url",f"https://youtube.com/channel/{c.get('channel_id','')}")
            tier = "mega" if c["subscribers"] and c["subscribers"]>=1_000_000 else \
                   "macro" if c["subscribers"] and c["subscribers"]>=100_000 else \
                   "mid" if c["subscribers"] and c["subscribers"]>=10_000 else "micro"
            rows += f'<tr class="creator-tr {tier}"><td class="cr-rank">{i}</td><td><a href="{e(link)}" target="_blank" rel="noopener" class="cr-link">{e(c["channel_name"][:32])}</a></td><td class="cr-subs">{subs}</td><td class="cr-country">{e(c.get("country","—"))}</td></tr>'
        secs.append(f"""<div class="card reveal full-width">
            <div class="card-label">🎬 Creator Ecosystem</div>
            <div class="tier-pills">{pills}</div>
            <div class="creator-note">~{fmt(total)} total YouTube videos</div>
            <div class="table-wrap"><table class="creator-table">
                <thead><tr><th>#</th><th>Channel</th><th>Subscribers</th><th>Country</th></tr></thead>
                <tbody>{rows}</tbody>
            </table></div></div>""")

    # ── Regional Distribution ──────────────────────────────────────
    regional = results.get("regional",{})
    gp_co  = regional.get("googleplay_countries",{})
    ios_co = regional.get("appstore_countries",{})
    web    = regional.get("web_summary","")
    if gp_co or ios_co or web:
        reg = ""
        if gp_co:
            reg += '<div class="region-title">🤖 Google Play</div><div class="region-rows">'
            for code,d in gp_co.items():
                reg += f'<div class="region-row"><span class="region-label">{e(d["label"])}</span><span class="region-score">⭐ {d["score"]}</span><span class="region-count">({fmt(d["ratings"])} ratings)</span></div>'
            reg += "</div>"
        if ios_co:
            reg += '<div class="region-title">🍎 App Store</div><div class="region-rows">'
            for code,d in ios_co.items():
                if d.get("available"):
                    reg += f'<div class="region-row"><span class="region-label">{e(d["label"])}</span><span class="region-score">⭐ {d["score"]}</span><span class="region-count">({fmt(d["ratings"])} ratings)</span></div>'
            reg += "</div>"
        if web:
            pct_m = re.findall(r'([A-Za-z\s]+):\s*(\d+)%', web)
            if pct_m:
                reg += '<div class="region-title">🌍 Download Distribution</div><div class="dist-chart">'
                for country, pct in pct_m[:6]:
                    reg += f'<div class="dist-row"><span class="dist-label">{e(country.strip())}</span><div class="dist-track"><div class="dist-fill" data-width="{pct}" style="width:0%"></div></div><span class="dist-pct">{pct}%</span></div>'
                reg += "</div>"
            else:
                reg += f'<div class="region-note">{e(web[:350])}</div>'
        secs.append(f'<div class="card reveal"><div class="card-label">🌍 Regional Distribution</div>{reg}</div>')

    # ── Player Deep Analysis ───────────────────────────────────────
    comment = results.get("yt_comment_analysis",{})
    if comment and "error" not in comment:
        sent   = comment.get("sentiment",{})
        kws    = comment.get("top_keywords_flat",[])
        ev_t   = comment.get("inferred_events",{}).get("event_video_titles",[])
        pps    = comment.get("painpoints",{}).get("top_painpoints",[])
        titles = comment.get("recent_video_titles",[])
        html_a = ""
        if sent:
            pp = sent.get("positive_pct",0); np_ = sent.get("negative_pct",0); nu = max(0,100-pp-np_)
            html_a += f"""<div class="sent-wrap">
                <div class="sent-labels"><span class="sent-pos">😊 {pp}% positive</span><span class="sent-neg">😞 {np_}% negative</span></div>
                <div class="sent-bar">
                    <div class="sent-seg s-pos" data-width="{pp}" style="width:0%"></div>
                    <div class="sent-seg s-neu" style="width:{nu}%"></div>
                    <div class="sent-seg s-neg" data-width="{np_}" style="width:0%"></div>
                </div></div>"""
        if kws:
            tags = "".join(f'<span class="kw-tag">{e(k)}</span>' for k in kws[:12])
            html_a += f'<div class="analysis-section"><div class="analysis-label">🔥 Hot Keywords</div><div class="kw-cloud">{tags}</div></div>'
        if ev_t:
            items = "".join(f"<li>{e(et)}</li>" for et in ev_t[:3])
            html_a += f'<div class="analysis-section"><div class="analysis-label">🎉 Recent Events</div><ul class="analysis-list">{items}</ul></div>'
        if pps:
            items = "".join(f'<li><strong>{e(pp["issue"])}</strong> [{pp["mentions"]}x] — {e(pp.get("example","")[:80])}</li>' for pp in pps[:4])
            html_a += f'<div class="analysis-section"><div class="analysis-label">🔧 Pain Points</div><ul class="analysis-list pain">{items}</ul></div>'
        if titles:
            items = "".join(f"<li>{e(tt)}</li>" for tt in titles[:5])
            html_a += f'<div class="analysis-section"><div class="analysis-label">📹 Recent Official Videos</div><ul class="analysis-list">{items}</ul></div>'
        secs.append(f'<div class="card reveal"><div class="card-label">💬 Player Deep Analysis</div>{html_a}</div>')

    # ── Assemble HTML ──────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{e(game_name)} — Game Benchmark</title>
<style>
{theme_vars}
{css}
</style>
</head>
<body>
<div class="header">
  <div class="header-badge">Game Benchmark Report · {e(now)}</div>
  <h1>{e(game_name)}</h1>
  <div class="header-meta">{t['emoji']} Powered by Game Benchmark Skill</div>
</div>
<div class="grid">
{"".join(secs)}
</div>
<div class="footer">Generated {e(now)} · Game Benchmark Skill</div>
<script>
function revealAll() {{
    document.querySelectorAll('.reveal').forEach(el => {{
        el.classList.add('visible');
        el.querySelectorAll('[data-width]').forEach(b => {{
            setTimeout(() => {{ b.style.width = b.dataset.width + '%'; }}, 200);
        }});
    }});
}}
// Scroll-triggered reveal
const observer = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
        if (entry.isIntersecting) {{
            entry.target.classList.add('visible');
            entry.target.querySelectorAll('[data-width]').forEach(el => {{
                setTimeout(() => {{ el.style.width = el.dataset.width + '%'; }}, 100);
            }});
        }}
    }});
}}, {{ threshold: 0.05 }});
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
// Trigger immediately — no waiting for fonts
revealAll();
// Also trigger after a short delay in case browser deferred rendering
setTimeout(revealAll, 300);
setTimeout(revealAll, 1000);
</script>
</body>
</html>"""

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
        return output_path
    return html


def save_report(game_name, results, output_dir=None):
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "reports"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w\-]', '_', game_name)
    fname = f"{safe}_benchmark_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    out   = output_dir / fname
    generate_html(game_name, results, str(out))
    return str(out)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 html_report.py results.json [output.html]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    path = save_report(data.get("game_name","Game"), data)
    print(f"✅ {path}")
