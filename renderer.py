"""
renderer.py — HTML report generator for the Requirements Traceability exercise.

You do NOT need to modify this file.

Usage:
    import renderer
    renderer.render(data)

This will:
  1. Write report.html in the current directory.
  2. Start a local web server on an available port (default 8080, falls back
     automatically if that port is busy).
  3. Open the report in your default browser.
  4. Keep the server running until you press Enter.

Port troubleshooting:
  If port 8080 is in use and the auto-fallback doesn't work for you, pass a
  different port explicitly:
      renderer.render(data, port=9090)

Data contract — `data` is a plain Python dict with this shape:
    {
        "title":    str,          # page heading
        "analyzed": int,          # total issues examined
        "traced":   int,          # issues with a linked PR
        "untraced": int,          # issues with no linked PR
        "issues": [               # one dict per issue
            {
                "number": int,
                "title":  str,
                "state":  str,    # "open" | "closed" | "?"
                "pr": None | {    # None means untraced
                    "number":     int,
                    "title":      str,
                    "commit_sha": str | None,
                    "commit_msg": str | None,
                }
            }
        ],
        "mermaid": str | None,    # raw Mermaid graph text; None = no diagram
        "warning": str | None,    # optional yellow banner message
    }
"""

import http.server
import os
import socket
import threading
import webbrowser

REPORT_FILE = "report.html"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render(data: dict, port: int = 8080) -> None:
    """Write report.html, start a local server, and open the browser."""
    html = _build_html(data)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    # Find a free port starting from the requested one.
    actual_port = _find_free_port(port)

    # Serve the current directory in a background daemon thread.
    handler = http.server.SimpleHTTPRequestHandler
    # Suppress the default "GET /report.html" log lines for cleaner output.
    handler.log_message = lambda *args: None
    server = http.server.HTTPServer(("127.0.0.1", actual_port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{actual_port}/{REPORT_FILE}"
    print(f"\n✅  Report written to {REPORT_FILE}")
    print(f"🌐  Serving at {url}")
    webbrowser.open(url)

    try:
        input("\nPress Enter to stop the server and exit...\n")
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_free_port(preferred: int) -> int:
    """Return `preferred` if it's free, otherwise find the next free port."""
    for candidate in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", candidate))
                return candidate
            except OSError:
                continue
    # Last resort: let the OS assign any free port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esc(text: str) -> str:
    """Minimal HTML escaping for user-supplied strings."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_html(data: dict) -> str:
    """Return a complete, self-contained HTML document as a string."""
    title    = _esc(data.get("title", "Traceability Report"))
    analyzed = data.get("analyzed", 0)
    traced   = data.get("traced", 0)
    untraced = data.get("untraced", 0)
    issues   = data.get("issues", [])
    mermaid  = data.get("mermaid")
    warning  = data.get("warning")

    gap_rate = round((untraced / analyzed * 100) if analyzed else 0)

    # ---- warning banner (optional) ----------------------------------------
    warning_html = ""
    if warning:
        warning_html = f"""
        <div class="banner-warning">
            ⚠️  {_esc(warning)}
        </div>"""

    # ---- stats bar ---------------------------------------------------------
    stats_html = f"""
        <div class="stats-bar">
            <div class="stat-tile">
                <span class="stat-num">{analyzed}</span>
                <span class="stat-label">Issues Analyzed</span>
            </div>
            <div class="stat-tile stat-green">
                <span class="stat-num">{traced}</span>
                <span class="stat-label">Traced (linked to PR)</span>
            </div>
            <div class="stat-tile stat-red">
                <span class="stat-num">{untraced}</span>
                <span class="stat-label">Untraced (no PR found)</span>
            </div>
            <div class="stat-tile">
                <span class="stat-num">{gap_rate}%</span>
                <span class="stat-label">Gap Rate</span>
            </div>
        </div>"""

    # ---- issue cards -------------------------------------------------------
    cards = []
    for issue in issues:
        num   = _esc(issue.get("number", "?"))
        ttl   = _esc(issue.get("title",  "Untitled"))
        state = _esc(issue.get("state",  "?"))
        pr    = issue.get("pr")

        if pr:
            pr_num  = _esc(pr.get("number", "?"))
            pr_ttl  = _esc(pr.get("title",  ""))
            sha     = pr.get("commit_sha")
            msg     = pr.get("commit_msg")

            commit_html = ""
            if sha:
                commit_html = f"""
                    <div class="commit-line">
                        💾 Commit <code>{_esc(sha)}</code>
                        {f'— {_esc(msg[:80])}' if msg else ''}
                    </div>"""

            pr_html = f"""
                <div class="pr-link">
                    🔗 PR <a href="https://github.com/psf/requests/pull/{pr_num}"
                            target="_blank">#{pr_num}</a>
                    — {pr_ttl}
                </div>
                {commit_html}"""
            border = "card-traced"
            badge  = '<span class="badge badge-traced">TRACED</span>'
        else:
            pr_html = '<div class="pr-missing">❌ No linked PR found</div>'
            border  = "card-untraced"
            badge   = '<span class="badge badge-untraced">UNTRACED</span>'

        cards.append(f"""
            <div class="card {border}">
                <div class="card-header">
                    <span class="issue-num">
                        <a href="https://github.com/psf/requests/issues/{num}"
                           target="_blank">#{num}</a>
                    </span>
                    <span class="issue-title">{ttl}</span>
                    <span class="state-tag">{state}</span>
                    {badge}
                </div>
                {pr_html}
            </div>""")

    cards_html = "\n".join(cards)

    # ---- mermaid block (Stretch tier only) ---------------------------------
    mermaid_html = ""
    if mermaid:
        mermaid_html = f"""
        <h2 class="section-heading">Issue → PR → Commit Graph</h2>
        <div class="mermaid-wrap">
            <pre class="mermaid">{_esc(mermaid)}</pre>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>"""

    # ---- full page ---------------------------------------------------------
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
          background: #f1f5f9; color: #1e293b; font-size: 15px; line-height: 1.6; }}
  a {{ color: #3b82f6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* header */
  .page-header {{ background: #0f172a; color: #f8fafc; padding: 24px 32px; }}
  .page-header h1 {{ font-size: 1.5rem; font-weight: 700; }}
  .page-header p  {{ color: #94a3b8; font-size: 0.9rem; margin-top: 4px; }}

  /* warning banner */
  .banner-warning {{ background: #fef9c3; border-left: 4px solid #f59e0b;
                     padding: 12px 20px; margin: 20px 32px 0;
                     border-radius: 4px; font-size: 0.9rem; color: #78350f; }}

  /* stats bar */
  .stats-bar {{ display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap; }}
  .stat-tile  {{ flex: 1; min-width: 120px; background: #fff; border-radius: 8px;
                 padding: 16px; text-align: center; border: 1px solid #e2e8f0; }}
  .stat-tile.stat-green {{ border-top: 3px solid #22c55e; }}
  .stat-tile.stat-red   {{ border-top: 3px solid #ef4444; }}
  .stat-num   {{ display: block; font-size: 2rem; font-weight: 700; color: #0f172a; }}
  .stat-label {{ display: block; font-size: 0.78rem; color: #64748b; margin-top: 2px; }}

  /* section heading */
  .section-heading {{ padding: 8px 32px 4px; font-size: 1.1rem;
                      color: #475569; font-weight: 600; }}

  /* cards */
  .cards {{ padding: 4px 32px 32px; display: flex; flex-direction: column; gap: 10px; }}
  .card {{ background: #fff; border-radius: 8px; padding: 14px 18px;
           border: 1px solid #e2e8f0; border-left: 5px solid #e2e8f0; }}
  .card-traced   {{ border-left-color: #22c55e; }}
  .card-untraced {{ border-left-color: #ef4444; }}
  .card-header {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }}
  .issue-num   {{ font-weight: 700; color: #0f172a; white-space: nowrap; }}
  .issue-title {{ flex: 1; color: #334155; }}
  .state-tag   {{ font-size: 0.75rem; color: #64748b; background: #f1f5f9;
                  padding: 2px 7px; border-radius: 99px; white-space: nowrap; }}
  .badge {{ font-size: 0.7rem; font-weight: 700; padding: 2px 8px;
            border-radius: 99px; white-space: nowrap; }}
  .badge-traced   {{ background: #dcfce7; color: #166534; }}
  .badge-untraced {{ background: #fee2e2; color: #991b1b; }}
  .pr-link, .pr-missing, .commit-line {{ margin-top: 6px; font-size: 0.875rem;
                                          color: #475569; }}
  .commit-line code {{ background: #f1f5f9; padding: 1px 5px;
                       border-radius: 3px; font-size: 0.8rem; }}

  /* mermaid */
  .mermaid-wrap {{ margin: 8px 32px 32px; background: #fff; border-radius: 8px;
                   padding: 24px; border: 1px solid #e2e8f0; overflow-x: auto; }}
</style>
</head>
<body>
<header class="page-header">
    <h1>{title}</h1>
    <p>Repository: <strong>psf/requests</strong> · Generated by trace_graph.py</p>
</header>
{warning_html}
{stats_html}
<h2 class="section-heading">Issues</h2>
<div class="cards">
{cards_html}
</div>
{mermaid_html}
</body>
</html>"""
