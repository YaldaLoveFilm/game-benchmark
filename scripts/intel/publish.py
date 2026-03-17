#!/usr/bin/env python3
"""
Publish HTML report to GitHub Pages.
Falls back to Cloudflare Quick Tunnel if GitHub token is unavailable.
"""
import os, re, subprocess, time, base64, json
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")
GITHUB_USER  = "YaldaLoveFilm"
GITHUB_REPO  = "game-benchmark-reports"
GITHUB_BRANCH = "main"
PAGES_BASE   = f"https://{GITHUB_USER.lower()}.github.io/{GITHUB_REPO}"

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


def publish_report(html_path: str) -> str:
    """
    Push HTML file to GitHub Pages repo.
    Returns the public URL.
    """
    html_path = Path(html_path)
    filename  = html_path.name

    try:
        import urllib.request, urllib.error

        content  = html_path.read_bytes()
        b64      = base64.b64encode(content).decode()

        # Check if file already exists (to get sha for update)
        api_url  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{filename}"
        headers  = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type":  "application/json",
            "User-Agent":    "game-benchmark-skill/1.0",
        }

        sha = None
        try:
            req  = urllib.request.Request(api_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            sha  = data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise

        payload = {
            "message": f"report: {filename}",
            "content": b64,
            "branch":  GITHUB_BRANCH,
        }
        if sha:
            payload["sha"] = sha

        body = json.dumps(payload).encode()
        req  = urllib.request.Request(api_url, data=body, headers=headers, method="PUT")
        resp = urllib.request.urlopen(req, timeout=20)
        result = json.loads(resp.read())

        pub_url = f"{PAGES_BASE}/{filename}"
        print(f"✅ Published to GitHub Pages: {pub_url}")
        return pub_url

    except Exception as ex:
        print(f"⚠️  GitHub Pages publish failed: {ex}")
        print("   Falling back to Cloudflare Quick Tunnel...")
        return _cloudflare_fallback(html_path)


def _cloudflare_fallback(html_path: Path) -> str:
    """Start a Cloudflare Quick Tunnel as fallback."""
    import socket, threading
    from http.server import SimpleHTTPRequestHandler, HTTPServer

    serve_dir = html_path.parent

    # Find free port
    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(serve_dir), **kw)
        def log_message(self, *_): pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    cf_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )
    tunnel_url = None
    deadline = time.time() + 30
    while time.time() < deadline:
        line = cf_proc.stderr.readline()
        m = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", line)
        if m:
            tunnel_url = m.group(0)
            break
    if tunnel_url:
        pub_url = f"{tunnel_url}/{html_path.name}"
        print(f"🌐 Cloudflare Tunnel: {pub_url}")
        return pub_url
    print("❌ Could not obtain tunnel URL")
    return f"file://{html_path}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 publish.py <report.html>")
        sys.exit(1)
    print(publish_report(sys.argv[1]))
