# /// script
# requires-python = ">=3.9"
# dependencies = ["markdown>=3.5"]
# ///
"""
Render a finished Markdown report into a Growgami-branded PDF.

The PDF leads with a call-to-action banner at the very top of the document:

    Go to https://growgami.com/contact for a deeper review and to learn
    about our agentic SEO done-for-you system

Branding follows the Growgami brand-guidelines skill: a monochrome grayscale
palette (#080808 ... #F9F9F9) and Geist Mono typography. The document uses
Growgami's dark identity — a near-black page, heavy Geist Mono titles, and
white text throughout.

Usage (zero-setup via uv — it installs the `markdown` dep automatically):

    uv run scripts/render_pdf.py seo-audit-2026-06-01.md
    uv run scripts/render_pdf.py report.md -o report.pdf --title "SEO Audit" --client "Acme Bank"
    uv run scripts/render_pdf.py report.md --html-only      # emit branded HTML, skip PDF

Rendering engine: any installed Chromium-family browser (Chrome, Edge, Brave,
Chromium) via headless `--print-to-pdf`. Point GROWGAMI_PDF_BROWSER at a binary
to override detection. If no browser is found the branded, print-ready HTML is
written next to the report so it can be opened and saved as PDF by hand.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import markdown  # provided by the uv inline-dependency block above

# --- exact CTA copy requested by the client ---------------------------------
CONTACT_URL = "https://growgami.com/contact"
CTA_TEXT = (
    "Go to {url} for a deeper review and to learn about "
    "our agentic SEO done-for-you system"
)

# --- Growgami brand tokens (from the brand-guidelines skill) -----------------
# Dark scale (near black)
NEAR_BLACK = "#080808"   # primary background, darkest
DARK_SURFACE = "#141414"  # dark surfaces (panels)
ELEVATED = "#1F1F1F"      # elevated dark surfaces (table headers, code)
DARK_BORDER = "#292929"   # borders on dark
SUBTLE = "#333333"        # subtle dark elements
# Light scale (white smoke)
LIGHT_SUBTLE = "#D6D6D6"  # secondary / muted text on dark
LIGHT_MUTED = "#E0E0E0"   # muted text
LIGHT_SURFACE = "#F5F5F5"
WHITE_SMOKE = "#F9F9F9"   # primary text on dark

FONT_STACK = (
    "'Geist Mono', ui-monospace, 'Cascadia Code', 'SFMono-Regular', "
    "'Menlo', 'Consolas', 'Liberation Mono', monospace"
)


def build_css() -> str:
    """The full stylesheet. Growgami dark identity: near-black page, heavy
    Geist Mono titles, white text, monochrome only."""
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&display=swap');

@page {{
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
}}

* {{ box-sizing: border-box; }}

/* Near-black is set on the root so it propagates to the full page canvas
   (every sheet, including the @page margins) in print. */
html {{
    background: {NEAR_BLACK};
}}

html, body {{
    margin: 0;
    padding: 0;
    background: {NEAR_BLACK};
    color: {WHITE_SMOKE};
    font-family: {FONT_STACK};
    font-weight: 400;
    font-size: 10.5pt;
    line-height: 1.6;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

/* --- Call-to-action banner: the first thing on the document --- */
.cta-banner {{
    background: {DARK_SURFACE};
    color: {WHITE_SMOKE};
    border: 1px solid {DARK_BORDER};
    padding: 18px 22px;
    border-radius: 8px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 18px;
    page-break-inside: avoid;
}}
.cta-banner .cta-mark {{
    font-weight: 700;
    font-size: 13pt;
    letter-spacing: 0.22em;
    white-space: nowrap;
    color: {WHITE_SMOKE};
    border-right: 1px solid {SUBTLE};
    padding-right: 18px;
}}
.cta-banner .cta-copy {{
    font-size: 10pt;
    line-height: 1.5;
    color: {LIGHT_SUBTLE};
}}
.cta-banner .cta-copy a {{
    color: {WHITE_SMOKE};
    font-weight: 600;
    text-decoration: underline;
    text-underline-offset: 2px;
}}

/* --- Cover / title block --- */
.cover {{
    border-bottom: 1px solid {DARK_BORDER};
    padding-bottom: 18px;
    margin-bottom: 32px;
}}
.cover .eyebrow {{
    font-size: 8.5pt;
    font-weight: 500;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: {LIGHT_SUBTLE};
    margin-bottom: 10px;
}}
.cover h1.cover-title {{
    font-size: 27pt;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.01em;
    margin: 0 0 12px 0;
    border: none;
    padding: 0;
    color: {WHITE_SMOKE};
}}
.cover .meta {{
    font-size: 9pt;
    color: {LIGHT_SUBTLE};
}}
.cover .meta span + span::before {{
    content: "  /  ";
    color: {SUBTLE};
}}

/* --- Body typography --- */
.content {{ color: {WHITE_SMOKE}; }}
.content h1, .content h2, .content h3, .content h4 {{
    font-weight: 700;
    line-height: 1.22;
    margin: 1.6em 0 0.5em 0;
    color: {WHITE_SMOKE};
    page-break-after: avoid;
}}
.content h1 {{ font-size: 18pt; border-bottom: 1px solid {DARK_BORDER}; padding-bottom: 8px; letter-spacing: -0.01em; }}
.content h2 {{ font-size: 14.5pt; border-bottom: 1px solid {DARK_BORDER}; padding-bottom: 5px; }}
.content h3 {{ font-size: 12pt; font-weight: 600; }}
.content h4 {{ font-size: 10.5pt; font-weight: 600; color: {LIGHT_MUTED}; }}
.content p {{ margin: 0.6em 0; color: {WHITE_SMOKE}; }}
.content a {{ color: {WHITE_SMOKE}; text-decoration: underline; text-underline-offset: 2px; }}
.content ul, .content ol {{ margin: 0.5em 0; padding-left: 1.5em; }}
.content li {{ margin: 0.28em 0; }}
.content strong {{ font-weight: 700; color: {WHITE_SMOKE}; }}
.content em {{ color: {LIGHT_MUTED}; }}
.content hr {{ border: none; border-top: 1px solid {DARK_BORDER}; margin: 1.8em 0; }}

.content blockquote {{
    margin: 1em 0;
    padding: 12px 18px;
    background: {DARK_SURFACE};
    border: 1px solid {DARK_BORDER};
    border-left: 3px solid {WHITE_SMOKE};
    border-radius: 4px;
    color: {LIGHT_SUBTLE};
}}
.content blockquote p {{ margin: 0.3em 0; color: {LIGHT_SUBTLE}; }}

.content code {{
    font-family: {FONT_STACK};
    background: {ELEVATED};
    border: 1px solid {DARK_BORDER};
    border-radius: 3px;
    padding: 0.5px 5px;
    font-size: 9.5pt;
    color: {LIGHT_MUTED};
}}
.content pre {{
    background: {DARK_SURFACE};
    color: {WHITE_SMOKE};
    border: 1px solid {DARK_BORDER};
    padding: 14px 16px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.5;
    page-break-inside: avoid;
}}
.content pre code {{ background: none; border: none; color: {WHITE_SMOKE}; padding: 0; }}

/* --- Tables (audit findings live here) --- */
.content table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 9.5pt;
    border: 1px solid {DARK_BORDER};
    page-break-inside: avoid;
}}
.content th {{
    background: {ELEVATED};
    color: {WHITE_SMOKE};
    font-weight: 600;
    text-align: left;
    padding: 9px 11px;
    border-bottom: 1px solid {SUBTLE};
}}
.content td {{
    border-bottom: 1px solid {DARK_BORDER};
    padding: 8px 11px;
    vertical-align: top;
    color: {WHITE_SMOKE};
}}
.content tr:nth-child(even) td {{ background: {DARK_SURFACE}; }}

/* --- Closing CTA (reinforced in the document flow) --- */
.cta-footer {{
    margin-top: 38px;
    padding: 22px;
    background: {DARK_SURFACE};
    color: {WHITE_SMOKE};
    border: 1px solid {DARK_BORDER};
    border-radius: 8px;
    text-align: center;
    page-break-inside: avoid;
}}
.cta-footer .headline {{ font-size: 12pt; font-weight: 700; margin-bottom: 7px; letter-spacing: 0.02em; color: {WHITE_SMOKE}; }}
.cta-footer .sub {{ font-size: 9.5pt; color: {LIGHT_SUBTLE}; }}
.cta-footer a {{ color: {WHITE_SMOKE}; font-weight: 600; }}

.colophon {{
    margin-top: 16px;
    text-align: center;
    font-size: 8pt;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {SUBTLE};
}}
"""


def cta_banner_html() -> str:
    link = f'<a href="{CONTACT_URL}">{html.escape(CONTACT_URL)}</a>'
    copy = CTA_TEXT.format(url=link)
    return (
        '<div class="cta-banner">'
        '<div class="cta-mark">GROWGAMI</div>'
        f'<div class="cta-copy">{copy}</div>'
        "</div>"
    )


def cta_footer_html() -> str:
    return (
        '<div class="cta-footer">'
        '<div class="headline">Want the deeper review?</div>'
        f'<div class="sub">Go to <a href="{CONTACT_URL}">{html.escape(CONTACT_URL)}</a> '
        "for a deeper review and to learn about our agentic SEO done-for-you system.</div>"
        "</div>"
        '<div class="colophon">Growgami — Agentic SEO for Neobanks &amp; Fintech</div>'
    )


def derive_title(md_text: str, fallback: str) -> str:
    """Use the report's first H1 as the title, else a cleaned filename."""
    for line in md_text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*#*\s*$", line.strip())
        if m:
            return m.group(1).strip()
    cleaned = re.sub(r"[-_]+", " ", fallback).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Report"


def strip_leading_h1(html_body: str) -> str:
    """The title is shown in the cover block, so drop a duplicate leading H1."""
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>", "", html_body, count=1, flags=re.DOTALL)


def build_document(md_text: str, title: str, client: str | None, report_date: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists", "toc", "nl2br"],
        output_format="html5",
    )
    body = strip_leading_h1(body)

    meta_parts = [f"<span>{html.escape(report_date)}</span>"]
    if client:
        meta_parts.insert(0, f"<span>{html.escape(client)}</span>")
    meta = "".join(meta_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{build_css()}</style>
</head>
<body>
{cta_banner_html()}
<div class="cover">
  <div class="eyebrow">Growgami · SEO Report</div>
  <h1 class="cover-title">{html.escape(title)}</h1>
  <div class="meta">{meta}</div>
</div>
<div class="content">
{body}
</div>
{cta_footer_html()}
</body>
</html>
"""


# --- browser detection / PDF rendering --------------------------------------
def find_browser() -> str | None:
    override = os.environ.get("GROWGAMI_PDF_BROWSER")
    if override and Path(override).exists():
        return override

    on_path = [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "microsoft-edge", "microsoft-edge-stable", "brave-browser", "chrome",
    ]
    for name in on_path:
        found = shutil.which(name)
        if found:
            return found

    candidates = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def render_pdf(browser: str, html_path: Path, pdf_path: Path) -> bool:
    src = html_path.resolve().as_uri()
    with tempfile.TemporaryDirectory(prefix="gg-pdf-") as profile:
        base = [
            browser,
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=6000",
            f"--print-to-pdf={pdf_path.resolve()}",
            src,
        ]
        # Newer Chromium wants --headless=new; older only knows --headless.
        for headless in ("--headless=new", "--headless"):
            cmd = [base[0], headless] + base[1:]
            try:
                subprocess.run(cmd, capture_output=True, timeout=120, check=False)
            except (subprocess.TimeoutExpired, OSError):
                continue
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown report to a Growgami-branded PDF.")
    parser.add_argument("input", help="Path to the finished Markdown report.")
    parser.add_argument("-o", "--output", help="Output PDF path (default: input with .pdf).")
    parser.add_argument("--title", help="Report title (default: first H1 / filename).")
    parser.add_argument("--client", help="Client name shown on the cover.")
    parser.add_argument("--date", dest="report_date", help="Date shown on the cover (default: today).")
    parser.add_argument("--html-only", action="store_true", help="Write branded HTML and skip PDF rendering.")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"error: input not found: {in_path}", file=sys.stderr)
        return 1

    md_text = in_path.read_text(encoding="utf-8")
    title = args.title or derive_title(md_text, in_path.stem)
    report_date = args.report_date or date.today().isoformat()

    document = build_document(md_text, title, args.client, report_date)
    html_path = in_path.with_suffix(".html")
    html_path.write_text(document, encoding="utf-8")

    if args.html_only:
        print(f"Branded HTML written: {html_path}")
        return 0

    pdf_path = Path(args.output) if args.output else in_path.with_suffix(".pdf")
    browser = find_browser()
    if not browser:
        print("No Chromium-family browser found for PDF rendering.", file=sys.stderr)
        print(f"Branded, print-ready HTML written instead: {html_path}", file=sys.stderr)
        print("Open it and 'Save as PDF', or set GROWGAMI_PDF_BROWSER to a Chrome/Edge binary.", file=sys.stderr)
        return 2

    if render_pdf(browser, html_path, pdf_path):
        html_path.unlink(missing_ok=True)
        print(f"Branded PDF written: {pdf_path}")
        return 0

    print(f"PDF rendering failed via {browser}.", file=sys.stderr)
    print(f"Branded HTML left for manual export: {html_path}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
