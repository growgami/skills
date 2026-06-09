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
from html.parser import HTMLParser
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


# --- HTML sanitizer ----------------------------------------------------------
# The report Markdown can contain raw HTML (e.g. content pasted from an audited
# or competitor site). markdown.markdown() passes that raw HTML through verbatim,
# and the result is rendered by headless Chrome with JS enabled — so an embedded
# <script>, an onerror= handler, or a javascript: URL would EXECUTE during PDF
# generation. To stop that without adding a dependency, the markdown output is
# run through this stdlib allowlist sanitizer: only the tags/attributes that
# markdown legitimately produces survive; everything else (including the entire
# contents of <script>/<style>) is dropped, and url-bearing attributes are
# scheme-checked.

# Tags markdown legitimately emits (extra + tables + code + toc + nl2br).
_ALLOWED_TAGS = frozenset({
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td",
    "pre", "code", "blockquote",
    "a", "strong", "em", "b", "i", "del", "span",
    "hr", "br", "img", "sup", "sub",
})

# Per-tag attribute allowlist. "class" is allowed broadly (markdown's toc /
# codehilite emit it); url attributes are scheme-checked separately.
_ALLOWED_ATTRS = {
    "a": {"href", "title", "class", "id"},
    "img": {"src", "alt", "title", "class"},
    "th": {"align", "class"},
    "td": {"align", "class"},
    "li": {"class", "id"},
    "ol": {"class", "start"},
    "ul": {"class"},
    "code": {"class"},
    "span": {"class"},
    "h1": {"id", "class"},
    "h2": {"id", "class"},
    "h3": {"id", "class"},
    "h4": {"id", "class"},
    "h5": {"id", "class"},
    "h6": {"id", "class"},
}
# Attributes allowed on any allowed tag.
_GLOBAL_ATTRS = frozenset({"class"})

# Tags whose entire text content must be discarded, not just the tag itself.
_DROP_CONTENT_TAGS = frozenset({"script", "style"})

# Void elements that never carry an end tag.
_VOID_TAGS = frozenset({"br", "hr", "img"})

# Attributes that carry a URL and must have their scheme validated.
_URL_ATTRS = frozenset({"href", "src"})
# Schemes considered safe for url-bearing attributes. Relative URLs and
# in-page anchors (which have no scheme) are also allowed.
_SAFE_SCHEMES = frozenset({"http", "https", "mailto", "tel"})
_SCHEME_RE = re.compile(r"^\s*([a-zA-Z][a-zA-Z0-9+.\-]*):")


def _is_safe_url(value: str) -> bool:
    """Allow relative URLs, anchors, and a small set of safe schemes; reject
    javascript:/data:/vbscript: and anything else with an explicit scheme."""
    if value is None:
        return False
    stripped = value.strip()
    # Strip HTML entities so e.g. "java&#115;cript:" can't sneak a scheme past.
    unescaped = html.unescape(stripped)
    m = _SCHEME_RE.match(unescaped)
    if not m:
        # No scheme → relative path, anchor (#...), query, or bare text. Safe.
        return True
    return m.group(1).lower() in _SAFE_SCHEMES


class _Sanitizer(HTMLParser):
    """Allowlist HTML sanitizer built on the stdlib parser. Keeps only the tags
    and attributes markdown produces; drops everything else; neutralizes unsafe
    URL schemes and all event-handler (on*) attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._out: list[str] = []
        # Depth counter for content we are actively discarding (inside script/style).
        self._suppress_depth = 0

    # -- helpers --
    def _emit(self, text: str) -> None:
        if self._suppress_depth == 0:
            self._out.append(text)

    def _render_attrs(self, tag: str, attrs: list[tuple[str, str | None]]) -> str:
        allowed = _ALLOWED_ATTRS.get(tag, set()) | _GLOBAL_ATTRS
        rendered: list[str] = []
        for name, value in attrs:
            lname = name.lower()
            # Drop every event handler outright.
            if lname.startswith("on"):
                continue
            if lname not in allowed:
                continue
            if lname in _URL_ATTRS and not _is_safe_url(value or ""):
                continue
            if value is None:
                rendered.append(f" {lname}")
            else:
                rendered.append(f' {lname}="{html.escape(value, quote=True)}"')
        return "".join(rendered)

    # -- HTMLParser callbacks --
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            self._suppress_depth += 1
            return
        if tag not in _ALLOWED_TAGS:
            return  # drop the tag, keep its (already-parsed) children
        attr_str = self._render_attrs(tag, attrs)
        if tag in _VOID_TAGS:
            self._emit(f"<{tag}{attr_str} />")
        else:
            self._emit(f"<{tag}{attr_str}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS or tag not in _ALLOWED_TAGS:
            return
        attr_str = self._render_attrs(tag, attrs)
        self._emit(f"<{tag}{attr_str} />")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            if self._suppress_depth > 0:
                self._suppress_depth -= 1
            return
        if tag not in _ALLOWED_TAGS or tag in _VOID_TAGS:
            return
        self._emit(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self._emit(html.escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self._emit(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._emit(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        # Comments can hide conditional-comment markup; drop them entirely.
        return

    def result(self) -> str:
        return "".join(self._out)


def sanitize_html(raw_html: str) -> str:
    """Run rendered-markdown HTML through the allowlist sanitizer so no
    executable or otherwise dangerous markup can reach the headless browser."""
    parser = _Sanitizer()
    parser.feed(raw_html)
    parser.close()
    return parser.result()


def build_css() -> str:
    """The full stylesheet. Growgami dark identity: near-black page, heavy
    Geist Mono titles, white text, monochrome only."""
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&display=swap');

/* Zero page margin so the page box IS the full physical sheet — the only way
   to get an edge-to-edge background in print (Chrome/Firefox never paint the
   @page margin band). Text insets come from body padding below, which is part
   of the body box and therefore painted near-black too. */
@page {{
    size: A4;
    margin: 0;
}}

* {{ box-sizing: border-box; }}

html {{
    background: {NEAR_BLACK};
}}

html, body {{
    margin: 0;
    background: {NEAR_BLACK};
    color: {WHITE_SMOKE};
    font-family: {FONT_STACK};
    font-weight: 400;
    font-size: 11pt;
    line-height: 1.72;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

body {{ padding: 0; }}

/* Full-bleed background layer. With @page margin:0 the page box is the whole
   sheet, so this fixed layer repeats on every page and covers it edge to edge
   (including the hairline the table layout would otherwise leave on the right). */
.page-bg {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: {NEAR_BLACK};
    z-index: -1;
}}

/* Per-page margins. Chrome cannot paint the @page margin band (root background
   and fixed layers are both clipped to the page box), so @page margin must be 0
   to get a full-bleed background. To still get a consistent top/bottom margin on
   EVERY page, the document is wrapped in a table: Chrome repeats <thead>/<tfoot>
   on each printed page, and their spacer rows reserve the vertical margin. The
   body cell supplies the horizontal margin. */
table.sheet {{
    width: 100%;
    border-collapse: collapse;
}}
table.sheet thead .sp {{ height: 16mm; }}
table.sheet tfoot .sp {{ height: 16mm; }}
td.sheet-body {{
    padding: 0 16mm;
    vertical-align: top;
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
    /* Never strand a heading at the foot of a page — keep it with what follows. */
    page-break-after: avoid;
    break-after: avoid;
    break-inside: avoid;
}}
.content h1 {{ font-size: 18pt; border-bottom: 1px solid {DARK_BORDER}; padding-bottom: 8px; letter-spacing: -0.01em; }}
.content h2 {{ font-size: 14.5pt; border-bottom: 1px solid {DARK_BORDER}; padding-bottom: 5px; }}
.content h3 {{ font-size: 12pt; font-weight: 600; }}
.content h4 {{ font-size: 10.5pt; font-weight: 600; color: {LIGHT_MUTED}; }}
.content p {{ margin: 0.6em 0; color: {WHITE_SMOKE}; orphans: 3; widows: 3; }}
/* Keep self-contained blocks from being sliced across a page break. */
.content blockquote, .content pre, .content table, .content li {{ break-inside: avoid; }}
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

/* Inline code kept deliberately subtle so technical tokens read as part of the
   prose, not as commands or buttons. */
.content code {{
    font-family: {FONT_STACK};
    background: {DARK_SURFACE};
    border-radius: 3px;
    padding: 0 3px;
    font-size: 0.95em;
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
    font-size: 9pt;
    font-weight: 500;
    letter-spacing: 0.08em;
    color: {LIGHT_SUBTLE};
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
        '<div class="headline">Want a deeper review?</div>'
        f'<div class="sub">Go to <a href="{CONTACT_URL}">{html.escape(CONTACT_URL)}</a> '
        "for a deeper review and to learn about our agentic SEO done-for-you system.</div>"
        "</div>"
        '<div class="colophon">Growgami — Venture growth partner for Neobanks &amp; Fintech</div>'
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
    # Strip any executable/dangerous HTML the source markdown may have carried
    # through (raw <script>, on* handlers, javascript:/data: URLs) before it can
    # reach the headless browser. Legitimate markdown output is untouched.
    body = sanitize_html(body)
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
<div class="page-bg"></div>
<table class="sheet">
<thead><tr><td><div class="sp"></div></td></tr></thead>
<tfoot><tr><td><div class="sp"></div></td></tr></tfoot>
<tbody><tr><td class="sheet-body">
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
</td></tr></tbody>
</table>
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
