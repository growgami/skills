# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Growth Scorecard — a reproducible, public-data Growth Score for a neobank/fintech.

Scores three dimensions from public signals only, deterministically, so anyone
re-running it on the same target gets the same number:

  * SEO      — raw-HTML/SSR content, title+meta, headings, schema, robots+sitemap,
               HTTPS, viewport, <html lang>, and Core Web Vitals (CrUX-banded).
  * ASO      — Apple App Store listing (rating, reviews, title/subtitle,
               screenshots, description, update freshness). Apple-only in v1.
  * AI-SEO   — readiness only: AI cite-bot access in robots.txt, machine-readable
               facts pages, AI-relevant schema, extractable structure, llms.txt.
               Never scores whether the site is actually cited by an AI.

The overall score is the simple mean of the dimensions that had any checks run.

Reproducibility crux: every Core Web Vitals signal is scored by CATEGORY BUCKET
(FAST/AVERAGE/SLOW), never by a raw millisecond/score number, so lab-run jitter
never moves the score. CrUX field data is preferred; Lighthouse lab data is the
fallback (bucketed against the standard CWV thresholds).

This script is stdlib-only (PEP-723 `dependencies = []`) so it runs identically
via `uv run` and plain `python`. It treats every fetched response as untrusted
DATA: HTML is parsed with html.parser (no JS), JSON with json.loads (never
eval/exec), and no fetched value is ever passed to a shell.

Usage:

    python scripts/scorecard.py monzo.com \
        --app-store "https://apps.apple.com/gb/app/monzo-bank/id434994682"

    uv run scripts/scorecard.py monzo.com --json-only -o web-health
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from typing import Optional

# --- constants ---------------------------------------------------------------

SCHEMA_VERSION = "1"
SCORE_VERSION = "1"

USER_AGENT = "GrowgamiGrowthScorecard/1.0 (+https://growgami.com)"
DEFAULT_TIMEOUT = 12
# PSI/Lighthouse responses routinely take 15-40s; give them a longer budget
# than the general fetch timeout so Core Web Vitals are not always skipped.
PSI_TIMEOUT = 60
MAX_BYTES = 3_000_000
MAX_REDIRECTS = 3

# AI cite-bots whose robots.txt access we score. CCBot is intentionally excluded
# from the penalty: blocking the Common Crawl bot is a common, defensible choice
# that does not by itself reduce live AI-answer citeability.
AI_CITE_BOTS = (
    "GPTBot",
    "ChatGPT-User",
    "PerplexityBot",
    "ClaudeBot",
    "anthropic-ai",
    "Google-Extended",
    "Bingbot",
)

# Schema types that signal AI-extractable, answer-engine-friendly content.
AI_RELEVANT_SCHEMA = (
    "FAQPage",
    "HowTo",
    "Article",
    "BlogPosting",
    "Organization",
    "FinancialProduct",
    "Product",
    "Review",
    "AggregateRating",
)

# Standard Core Web Vitals lab thresholds (good / needs-improvement boundary).
# Used only when CrUX field data is unavailable, and only to assign a 3-band
# bucket — the raw number is never scored directly.
CWV_LAB_THRESHOLDS = {
    # metric: (good_max, poor_min)  — value <= good_max => FAST,
    #                                  value >= poor_min => SLOW, else AVERAGE
    "LCP": (2500.0, 4000.0),   # milliseconds
    "INP": (200.0, 500.0),     # milliseconds
    "CLS": (0.1, 0.25),        # unitless
}

# Hostname must be a dotted name with a real TLD; rejects bare hosts and most junk.
HOSTNAME_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")
IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


# --- fetch layer -------------------------------------------------------------

@dataclass
class FetchResult:
    """The outcome of a single GET. `ok` is True only on a 2xx with a body.
    This type NEVER carries an exception; safe_get catches everything."""
    ok: bool
    status: Optional[int]
    url: str
    final_url: str
    body: str
    error: Optional[str] = None


def _same_or_subdomain(original_host: str, new_host: str) -> bool:
    """A redirect may stay on the same host or move to a subdomain of it (or its
    parent registrable-ish domain). We allow new_host that ends with the original
    host, or whose last two labels match the original's last two labels."""
    original_host = (original_host or "").lower().rstrip(".")
    new_host = (new_host or "").lower().rstrip(".")
    if not new_host:
        return False
    if new_host == original_host:
        return True
    if new_host.endswith("." + original_host):
        return True
    if original_host.endswith("." + new_host):
        return True
    o_parts = original_host.split(".")
    n_parts = new_host.split(".")
    if len(o_parts) >= 2 and len(n_parts) >= 2:
        return o_parts[-2:] == n_parts[-2:]
    return False


class _BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Cap redirects and reject cross-host / non-http(s) hops.

    urllib's default handler follows redirects freely; we constrain it so a
    malicious or misconfigured target can't bounce us to an arbitrary scheme or
    an unrelated host (SSRF-style surprises). The redirect count is enforced by
    urllib's own max_redirections, which we lower via the override below.
    """

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            new_parts = _split_url(newurl)
        except ValueError:
            return None
        scheme = new_parts[0].lower()
        if scheme not in ("http", "https"):
            return None
        old_host = req.host if hasattr(req, "host") else ""
        new_host = new_parts[1]
        if not _same_or_subdomain(old_host, new_host):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _split_url(url: str):
    """Return (scheme, host, rest) without importing urllib.parse for hostname
    games we don't need. Raises ValueError on something that isn't a URL."""
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*)://([^/?#]+)(.*)$", url)
    if not m:
        raise ValueError(f"not a URL: {url!r}")
    return m.group(1), m.group(2).lower(), m.group(3)


_OPENER = urllib.request.build_opener(_BoundedRedirectHandler())


def safe_get(url: str, timeout: int = DEFAULT_TIMEOUT) -> FetchResult:
    """A single, bounded GET that NEVER raises.

    Sets a User-Agent, caps the response at MAX_BYTES, follows at most
    MAX_REDIRECTS same/subdomain http(s) redirects, and converts every possible
    failure (URLError, HTTPError, timeout, decode error) into a FetchResult.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BYTES)
            status = getattr(resp, "status", None) or resp.getcode()
            final_url = resp.geturl()
            charset = resp.headers.get_content_charset() or "utf-8"
            try:
                body = raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                body = raw.decode("utf-8", errors="replace")
            return FetchResult(
                ok=200 <= (status or 0) < 300,
                status=status,
                url=url,
                final_url=final_url,
                body=body,
            )
    except urllib.error.HTTPError as exc:
        # An HTTP error still has a status; read a bounded body for inspection.
        try:
            raw = exc.read(MAX_BYTES)
            body = raw.decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return FetchResult(
            ok=False,
            status=exc.code,
            url=url,
            final_url=getattr(exc, "url", url) or url,
            body=body,
            error=f"HTTP {exc.code}",
        )
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        return FetchResult(False, None, url, url, "", error=f"network error: {reason}")
    except Exception as exc:  # absolute backstop — safe_get must never raise
        return FetchResult(False, None, url, url, "", error=f"unexpected: {exc}")


def normalize_domain(raw: str) -> Optional[str]:
    """Turn user input into a bare lowercase hostname, or None if invalid.

    Strips scheme/path/port, lowercases, and validates against HOSTNAME_RE.
    Rejects embedded credentials (`@`), IP literals (we want a real registrable
    domain), and obvious private/loopback ranges. Returning None lets the CLI
    exit BEFORE any network call.
    """
    if not raw or not isinstance(raw, str):
        return None
    value = raw.strip()
    # Strip scheme.
    value = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", "", value)
    # Drop anything after the authority (path/query/fragment).
    value = re.split(r"[/?#]", value, maxsplit=1)[0]
    # Reject credentials.
    if "@" in value:
        return None
    # Strip a trailing port.
    value = re.sub(r":\d+$", "", value)
    value = value.strip().rstrip(".").lower()
    if not value:
        return None
    if not HOSTNAME_RE.match(value):
        return None
    # Reject IP literals — we want a registrable domain, not a host.
    if IPV4_RE.match(value):
        return None
    # Reject obvious private / loopback names.
    if value in ("localhost",) or value.endswith(".localhost"):
        return None
    return value


# --- HTML parsing ------------------------------------------------------------

class _PageParser(HTMLParser):
    """Capture SEO-relevant signals from RAW HTML (no JS executed).

    Everything here is read-only extraction of untrusted markup: tag/attribute
    presence and text content. No fetched value is executed or shelled out.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.meta_viewport: Optional[str] = None
        self.html_lang: Optional[str] = None
        self.h1_count = 0
        self.h2_count = 0
        self.h3_count = 0
        self.list_count = 0   # <ul> + <ol>
        self.table_count = 0
        self.jsonld_blocks: list[str] = []
        self.body_word_count = 0

        self._in_title = False
        self._title_parts: list[str] = []
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        # Tags whose text we exclude from the body word count.
        self._skip_text_depth = 0
        self._skip_tags = {"script", "style", "noscript", "template"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and self.html_lang is None:
            lang = a.get("lang")
            if lang:
                self.html_lang = lang.strip()
        elif tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag == "meta":
            name = a.get("name", "").lower()
            if name == "description" and self.meta_description is None:
                self.meta_description = a.get("content", "").strip()
            elif name == "viewport" and self.meta_viewport is None:
                self.meta_viewport = a.get("content", "").strip()
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "h2":
            self.h2_count += 1
        elif tag == "h3":
            self.h3_count += 1
        elif tag in ("ul", "ol"):
            self.list_count += 1
        elif tag == "table":
            self.table_count += 1
        elif tag == "script":
            stype = a.get("type", "").lower().strip()
            if stype == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_parts = []
        if tag in self._skip_tags:
            self._skip_text_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title" and self._in_title:
            self._in_title = False
            text = "".join(self._title_parts).strip()
            if text and self.title is None:
                self.title = text
        elif tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            block = "".join(self._jsonld_parts).strip()
            if block:
                self.jsonld_blocks.append(block)
        if tag in self._skip_tags and self._skip_text_depth > 0:
            self._skip_text_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_jsonld:
            self._jsonld_parts.append(data)
        if self._skip_text_depth == 0:
            words = data.split()
            if words:
                self.body_word_count += len(words)


def parse_page(html_text: str) -> _PageParser:
    parser = _PageParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        # A malformed page must not crash the run; return whatever we captured.
        pass
    return parser


def extract_schema_types(jsonld_blocks: list[str]) -> set[str]:
    """Pull @type values from JSON-LD blocks. Each block is parsed in its own
    try/except (one broken block can't take down the rest). json.loads only —
    never eval/exec."""
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                found.add(t)
            elif isinstance(t, list):
                for item in t:
                    if isinstance(item, str):
                        found.add(item)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for block in jsonld_blocks:
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
        try:
            walk(data)
        except Exception:
            continue
    return found


# --- scoring helpers ---------------------------------------------------------

@dataclass
class Check:
    """A single deterministic check. `points` of `max` earned; `note` explains."""
    value: object
    points: float
    max: float
    note: str

    def as_dict(self) -> dict:
        return {
            "value": self.value,
            "points": round(self.points, 2),
            "max": self.max,
            "note": self.note,
        }


@dataclass
class Dimension:
    name: str
    checks: dict[str, Check] = field(default_factory=dict)
    available: bool = True
    skip_reason: Optional[str] = None

    def add(self, key: str, check: Check) -> None:
        self.checks[key] = check

    def score(self) -> Optional[float]:
        """Normalize earned/available-max to 0-100. Skipped checks (max == 0)
        drop out and the remainder renormalizes. Returns None if nothing ran."""
        total_max = sum(c.max for c in self.checks.values())
        total_earned = sum(c.points for c in self.checks.values())
        if total_max <= 0:
            return None
        return round((total_earned / total_max) * 100.0, 1)

    def as_dict(self) -> dict:
        return {
            "score": self.score(),
            "available": self.available,
            "checks": {k: c.as_dict() for k, c in self.checks.items()},
        }


def cwv_bucket_points(category: str, full: float) -> tuple[float, str]:
    """Map a CrUX/lab category bucket to points. FAST=full, AVERAGE=half,
    SLOW/other=0. Always bucket-based so re-runs are identical."""
    cat = (category or "").upper()
    if cat == "FAST":
        return full, "FAST"
    if cat == "AVERAGE":
        return full / 2.0, "AVERAGE"
    return 0.0, "SLOW" if cat == "SLOW" else (cat or "UNKNOWN")


def lab_bucket(metric: str, value: float) -> str:
    """Bucket a raw lab numericValue into FAST/AVERAGE/SLOW using the standard
    CWV thresholds. The number itself is never scored — only this bucket is."""
    good_max, poor_min = CWV_LAB_THRESHOLDS[metric]
    if value <= good_max:
        return "FAST"
    if value >= poor_min:
        return "SLOW"
    return "AVERAGE"


# --- robots.txt parsing ------------------------------------------------------

def parse_robots(text: str) -> dict:
    """Parse robots.txt into per-user-agent disallow lists and sitemap refs.
    Returns {agents: {ua_lower: [disallow_paths]}, sitemaps: [...]}.
    Pure text parsing of untrusted data — no execution."""
    agents: dict[str, list[str]] = {}
    sitemaps: list[str] = []
    current_uas: list[str] = []
    # Track whether the previous non-blank directive was user-agent (to group
    # consecutive user-agent lines into one block per robots.txt spec).
    last_was_ua = False
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            last_was_ua = False
            continue
        field_name, _, value = line.partition(":")
        field_name = field_name.strip().lower()
        value = value.strip()
        if field_name == "user-agent":
            if not last_was_ua:
                current_uas = []
            ua = value.lower()
            current_uas.append(ua)
            agents.setdefault(ua, [])
            last_was_ua = True
        elif field_name == "disallow":
            for ua in current_uas:
                agents.setdefault(ua, []).append(value)
            last_was_ua = False
        elif field_name == "sitemap":
            sitemaps.append(value)
            last_was_ua = False
        else:
            last_was_ua = False
    return {"agents": agents, "sitemaps": sitemaps}


def robots_blocks_root(robots: dict, ua: str) -> bool:
    """True if the given user-agent (falling back to *) is blocked from / .
    A blanket `Disallow: /` (or empty-path-less full block) counts."""
    agents = robots["agents"]
    rules = agents.get(ua.lower())
    if rules is None:
        rules = agents.get("*")
    if rules is None:
        return False
    for path in rules:
        if path == "/":
            return True
    return False


# --- SEO dimension -----------------------------------------------------------

def score_seo(domain: str, timeout: int, do_cwv: bool, strategy: str,
              warnings: list, skipped: list) -> Dimension:
    dim = Dimension("seo")
    https_url = f"https://{domain}/"
    http_url = f"http://{domain}/"

    # Primary fetch over HTTPS.
    home = safe_get(https_url, timeout)
    if not home.ok:
        # Try HTTP as a last resort so we can still parse the page.
        home_http = safe_get(http_url, timeout)
        if home_http.ok:
            home = home_http

    if not home.ok:
        dim.available = False
        dim.skip_reason = f"could not fetch homepage ({home.error or 'no 2xx'})"
        skipped.append({"dimension": "seo", "reason": dim.skip_reason})
        return dim

    page = parse_page(home.body)
    schema_types = extract_schema_types(page.jsonld_blocks)

    # --- SSR / raw-HTML content (12) ---
    words = page.body_word_count
    if words >= 250:
        pts = 12.0
    else:
        pts = round(12.0 * min(words, 250) / 250.0, 2)
    dim.add("ssr_content", Check(
        value=words, points=pts, max=12,
        note=f"{words} words in raw HTML (>=250 for full credit)",
    ))

    # --- Title + meta description (12) ---
    title = page.title or ""
    title_len = len(title.strip())
    title_pts = 6.0 if (title_len >= 15 and title_len <= 60) else 0.0
    meta = page.meta_description or ""
    meta_len = len(meta.strip())
    meta_pts = 6.0 if (meta_len >= 50 and meta_len <= 160) else 0.0
    dim.add("title_meta", Check(
        value={"title_len": title_len, "meta_len": meta_len},
        points=title_pts + meta_pts, max=12,
        note=("title present 15-60 chars (6) + meta present 50-160 chars (6); "
              f"title={title_len} meta={meta_len}"),
    ))

    # --- Headings (8): exactly one H1 (5) + at least one H2 (3) ---
    h1_pts = 5.0 if page.h1_count == 1 else 0.0
    h2_pts = 3.0 if page.h2_count >= 1 else 0.0
    dim.add("headings", Check(
        value={"h1": page.h1_count, "h2": page.h2_count, "h3": page.h3_count},
        points=h1_pts + h2_pts, max=8,
        note=(f"exactly one raw H1 (5): {page.h1_count}; >=1 H2 (3): {page.h2_count}"),
    ))

    # --- JSON-LD schema present (8) ---
    schema_pts = 8.0 if schema_types else 0.0
    dim.add("schema_present", Check(
        value=sorted(schema_types), points=schema_pts, max=8,
        note=("raw-HTML JSON-LD present (JS-injected schema not visible here; "
              "confirm in a browser)"),
    ))

    # --- Viewport (6) ---
    vp_pts = 6.0 if (page.meta_viewport and "width" in page.meta_viewport.lower()) else 0.0
    dim.add("viewport", Check(
        value=page.meta_viewport or None, points=vp_pts, max=6,
        note="mobile viewport meta present",
    ))

    # --- <html lang> (8) ---
    lang_pts = 8.0 if (page.html_lang and len(page.html_lang) >= 2) else 0.0
    dim.add("html_lang", Check(
        value=page.html_lang or None, points=lang_pts, max=8,
        note="<html lang> attribute present",
    ))

    # --- HTTPS + redirect (8): https serves (4) + http->https (4) ---
    https_serves = 4.0 if home.final_url.lower().startswith("https://") else 0.0
    http_redirect = safe_get(http_url, timeout)
    redirects_to_https = (
        4.0 if (http_redirect.ok and http_redirect.final_url.lower().startswith("https://"))
        else 0.0
    )
    dim.add("https_redirect", Check(
        value={"https_serves": bool(https_serves), "http_to_https": bool(redirects_to_https)},
        points=https_serves + redirects_to_https, max=8,
        note="HTTPS serves (4) + HTTP redirects to HTTPS (4)",
    ))

    # --- robots.txt + sitemap (8): robots ok (4) + sitemap returns XML (4) ---
    robots_res = safe_get(f"https://{domain}/robots.txt", timeout)
    robots_pts = 0.0
    robots_data = {"agents": {}, "sitemaps": []}
    if robots_res.ok and robots_res.body.strip():
        robots_data = parse_robots(robots_res.body)
        # "ok" = reachable and not a blanket Disallow: / for the default agent.
        if not robots_blocks_root(robots_data, "*"):
            robots_pts = 4.0
    sitemap_pts = 0.0
    sitemap_urls = list(robots_data.get("sitemaps") or [])
    sitemap_candidates = sitemap_urls + [f"https://{domain}/sitemap.xml"]
    sitemap_checked = None
    for sm_url in sitemap_candidates:
        sm = safe_get(sm_url, timeout)
        sitemap_checked = sm_url
        if sm.ok and ("<urlset" in sm.body or "<sitemapindex" in sm.body or "<?xml" in sm.body):
            sitemap_pts = 4.0
            break
    dim.add("robots_sitemap", Check(
        value={"robots_ok": bool(robots_pts), "sitemap_xml": bool(sitemap_pts),
               "sitemap_checked": sitemap_checked},
        points=robots_pts + sitemap_pts, max=8,
        note="robots.txt reachable & no blanket Disallow:/ (4) + sitemap returns XML (4)",
    ))

    # --- Core Web Vitals (28): LCP 12 / INP 8 / CLS 8, CrUX-banded ---
    if do_cwv:
        cwv_checks = score_cwv(domain, strategy, timeout, warnings)
        if cwv_checks is None:
            skipped.append({
                "check": "cwv",
                "dimension": "seo",
                "reason": "PageSpeed Insights unavailable; CWV skipped and SEO renormalized",
            })
        else:
            for key, chk in cwv_checks.items():
                dim.add(key, chk)
    else:
        skipped.append({
            "check": "cwv",
            "dimension": "seo",
            "reason": "CWV skipped by --no-cwv",
        })

    return dim


def score_cwv(domain: str, strategy: str, timeout: int,
              warnings: list) -> Optional[dict]:
    """Call PageSpeed Insights and return CrUX-banded CWV checks, or None to skip.

    Prefers CrUX field data (loadingExperience). Falls back to Lighthouse lab
    numericValue bucketed against standard thresholds. ALWAYS scores the 3-band
    bucket, never a raw number, so re-runs are identical.
    """
    url = f"https://{domain}/"
    psi = (
        "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        f"?url={url}&strategy={strategy}"
    )
    key = os.environ.get("GROWGAMI_PSI_KEY")
    if key:
        psi += f"&key={key}"

    res = safe_get(psi, PSI_TIMEOUT)
    if not (res.ok and res.body):
        # One retry after a 2s backoff (deterministic-enough; bucket scoring
        # means a successful retry yields the same points).
        if res.status == 429 or not res.ok:
            try:
                import time
                time.sleep(2)
            except Exception:
                pass
            res = safe_get(psi, PSI_TIMEOUT)
        if not (res.ok and res.body):
            warnings.append(
                "PageSpeed Insights unavailable (set GROWGAMI_PSI_KEY for higher "
                "rate limits); Core Web Vitals were skipped."
            )
            return None

    try:
        data = json.loads(res.body)
    except (json.JSONDecodeError, ValueError):
        warnings.append("PageSpeed Insights returned unparseable JSON; CWV skipped.")
        return None

    # Metric key map: our metric -> (CrUX field key, Lighthouse audit id)
    field_keys = {
        "LCP": ("LARGEST_CONTENTFUL_PAINT_MS", "largest-contentful-paint"),
        "INP": ("INTERACTION_TO_NEXT_PAINT", "interaction-to-next-paint"),
        "CLS": ("CUMULATIVE_LAYOUT_SHIFT_SCORE", "cumulative-layout-shift"),
    }
    maxima = {"LCP": 12.0, "INP": 8.0, "CLS": 8.0}

    # Prefer CrUX field data: loadingExperience, then originLoadingExperience.
    field = data.get("loadingExperience", {}) or {}
    field_metrics = field.get("metrics") or {}
    if not field_metrics:
        origin = data.get("originLoadingExperience", {}) or {}
        field_metrics = origin.get("metrics") or {}

    checks: dict[str, Check] = {}
    source = None

    if field_metrics:
        source = "field"
        for metric, (crux_key, _audit_id) in field_keys.items():
            entry = field_metrics.get(crux_key) or {}
            category = entry.get("category")
            if category is None:
                # Missing this metric in field data — bucket as unknown -> 0.
                pts, band = 0.0, "UNKNOWN"
            else:
                pts, band = cwv_bucket_points(category, maxima[metric])
            checks[f"cwv_{metric.lower()}"] = Check(
                value={"category": band, "source": "field"},
                points=pts, max=maxima[metric],
                note=f"CrUX field {metric} category {band} (FAST=full/AVERAGE=half/SLOW=0)",
            )
    else:
        # Lab fallback: Lighthouse numericValue -> standard-threshold bucket.
        source = "lab"
        warnings.append(
            "No CrUX field data for this origin; Core Web Vitals scored from "
            "Lighthouse lab data (bucketed against standard thresholds)."
        )
        audits = (data.get("lighthouseResult", {}) or {}).get("audits", {}) or {}
        for metric, (_crux_key, audit_id) in field_keys.items():
            audit = audits.get(audit_id) or {}
            numeric = audit.get("numericValue")
            if numeric is None:
                pts, band = 0.0, "UNKNOWN"
                value = {"category": band, "source": "lab"}
            else:
                band = lab_bucket(metric, float(numeric))
                pts, _ = cwv_bucket_points(band, maxima[metric])
                value = {"category": band, "source": "lab"}
            checks[f"cwv_{metric.lower()}"] = Check(
                value=value, points=pts, max=maxima[metric],
                note=f"Lighthouse lab {metric} bucketed {band} (FAST=full/AVERAGE=half/SLOW=0)",
            )

    # Stamp the source onto every CWV check value for transparency.
    for chk in checks.values():
        if isinstance(chk.value, dict):
            chk.value["cwv_source"] = source
    return checks


# --- ASO dimension (Apple-only in v1) ----------------------------------------

def _slug_term(app_store_url: str) -> str:
    """Derive a human-readable search term from an App Store URL slug.
    e.g. .../app/monzo-bank/id434994682 -> 'monzo bank'."""
    parts = [p for p in app_store_url.rstrip("/").split("/") if p]
    # Prefer the segment right before an /id... segment (the app name slug).
    slug = ""
    for i, p in enumerate(parts):
        if re.match(r"^id\d+$", p) and i > 0:
            slug = parts[i - 1]
            break
    if not slug:
        slug = parts[-1] if parts else app_store_url
    slug = re.sub(r"[^a-zA-Z0-9 ]", " ", slug).strip()
    return slug or app_store_url


def parse_apple_url(app_store_url: str) -> dict:
    """Extract Apple app id + country from an App Store URL, or a search term.
    Returns {"id"/"term": ..., "country": ..., "slug": ...}. The slug is always
    derived so an id lookup that finds nothing can fall back to a name search."""
    country = "us"
    m_cc = re.search(r"apps\.apple\.com/([a-z]{2})/", app_store_url, re.IGNORECASE)
    if m_cc:
        country = m_cc.group(1).lower()
    slug = _slug_term(app_store_url)
    m_id = re.search(r"/id(\d+)", app_store_url)
    if m_id:
        return {"id": m_id.group(1), "country": country, "slug": slug}
    return {"term": slug, "country": country, "slug": slug}


def score_aso(app_store_url: str, timeout: int, warnings: list,
              skipped: list) -> Dimension:
    dim = Dimension("aso")
    parsed = parse_apple_url(app_store_url)
    country = parsed["country"]

    def _search_url() -> str:
        term = urllib.request.quote(parsed.get("term") or parsed.get("slug") or "")
        return (
            f"https://itunes.apple.com/search?term={term}&country={country}"
            "&entity=software&limit=1"
        )

    if "id" in parsed:
        lookup = f"https://itunes.apple.com/lookup?id={parsed['id']}&country={country}"
    else:
        lookup = _search_url()

    res = safe_get(lookup, timeout)
    if not (res.ok and res.body):
        dim.available = False
        dim.skip_reason = f"iTunes lookup failed ({res.error or 'no 2xx'})"
        skipped.append({"dimension": "aso", "reason": dim.skip_reason})
        return dim

    try:
        data = json.loads(res.body)
    except (json.JSONDecodeError, ValueError):
        dim.available = False
        dim.skip_reason = "iTunes lookup returned unparseable JSON"
        skipped.append({"dimension": "aso", "reason": dim.skip_reason})
        return dim

    results = data.get("results") or []
    # An id lookup can return nothing if the id is stale or storefront-specific;
    # fall back to a name search derived from the URL slug (spec: bare name ->
    # search endpoint). Deterministic: limit=1 returns the top match.
    if not results and "id" in parsed and (parsed.get("slug")):
        fb = safe_get(_search_url(), timeout)
        if fb.ok and fb.body:
            try:
                results = (json.loads(fb.body).get("results") or [])
            except (json.JSONDecodeError, ValueError):
                results = []
        if results:
            warnings.append(
                f"App id {parsed['id']} returned no iTunes result; matched by name "
                f"search ('{parsed.get('slug')}') instead."
            )

    if not results:
        dim.available = False
        dim.skip_reason = "no matching app found in iTunes lookup"
        skipped.append({"dimension": "aso", "reason": dim.skip_reason})
        return dim

    app = results[0]

    # --- Rating (25), rounded to 0.1 first ---
    raw_rating = app.get("averageUserRating")
    if raw_rating is None:
        rating_pts, rating_val = 0.0, None
    else:
        rating_val = round(float(raw_rating), 1)
        if rating_val >= 4.5:
            rating_pts = 25.0
        elif rating_val >= 4.0:
            rating_pts = 18.0
        elif rating_val >= 3.5:
            rating_pts = 10.0
        else:
            rating_pts = 0.0
    dim.add("rating", Check(
        value=rating_val, points=rating_pts, max=25,
        note=">=4.5 full /4.0-4.49 18 /3.5-3.99 10 /<3.5 0 (rating rounded to 0.1)",
    ))

    # --- Review count tier (20) ---
    reviews = app.get("userRatingCount")
    rc = int(reviews) if isinstance(reviews, (int, float)) else 0
    if rc >= 100_000:
        rc_pts = 20.0
    elif rc >= 10_000:
        rc_pts = 15.0
    elif rc >= 1_000:
        rc_pts = 10.0
    else:
        rc_pts = 4.0
    dim.add("review_count", Check(
        value=rc, points=rc_pts, max=20,
        note=">=100k full /10k-100k 15 /1k-10k 10 /<1k 4",
    ))

    # --- Title + subtitle (20): title <=30 (10) + subtitle present <=30 (10) ---
    name = (app.get("trackName") or "").strip()
    title_pts = 10.0 if (name and len(name) <= 30) else 0.0
    # iTunes lookup does not expose subtitle; treat as not present.
    subtitle = (app.get("subtitle") or "").strip()
    subtitle_pts = 10.0 if (subtitle and len(subtitle) <= 30) else 0.0
    dim.add("title_subtitle", Check(
        value={"title": name, "title_len": len(name),
               "subtitle_len": len(subtitle)},
        points=title_pts + subtitle_pts, max=20,
        note=("title non-empty <=30 chars (10) + subtitle present <=30 (10); "
              "iTunes lookup may not expose subtitle"),
    ))

    # --- Screenshots (15): >=5 full /3-4 9 /<3 0 ---
    shots = app.get("screenshotUrls") or []
    n_shots = len(shots) if isinstance(shots, list) else 0
    if n_shots >= 5:
        shot_pts = 15.0
    elif n_shots >= 3:
        shot_pts = 9.0
    else:
        shot_pts = 0.0
    dim.add("screenshots", Check(
        value=n_shots, points=shot_pts, max=15,
        note=">=5 full /3-4 9 /<3 0 (count only; quality craft deferred to aso skill)",
    ))

    # --- Description (10): >=500 full />=100 5 /else 0 ---
    desc = (app.get("description") or "").strip()
    dlen = len(desc)
    if dlen >= 500:
        desc_pts = 10.0
    elif dlen >= 100:
        desc_pts = 5.0
    else:
        desc_pts = 0.0
    dim.add("description", Check(
        value=dlen, points=desc_pts, max=10,
        note=">=500 chars full />=100 5 /else 0",
    ))

    # --- Update freshness (10): <=30d full /<=90d 7 /<=180d 3 /older 0 ---
    updated = app.get("currentVersionReleaseDate") or app.get("releaseDate")
    fresh_pts, age_days = 0.0, None
    if updated:
        try:
            dt = datetime.strptime(updated[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dt).days
            if age_days <= 30:
                fresh_pts = 10.0
            elif age_days <= 90:
                fresh_pts = 7.0
            elif age_days <= 180:
                fresh_pts = 3.0
            else:
                fresh_pts = 0.0
        except (ValueError, TypeError):
            age_days = None
    dim.add("update_freshness", Check(
        value=age_days, points=fresh_pts, max=10,
        note="<=30d full /<=90d 7 /<=180d 3 /older 0",
    ))

    return dim


# --- AI-SEO dimension --------------------------------------------------------

def score_ai_seo(domain: str, timeout: int, seo_page: Optional[_PageParser],
                 schema_types: Optional[set], warnings: list,
                 skipped: list) -> Dimension:
    dim = Dimension("ai_seo")

    # Re-fetch the homepage if SEO didn't hand one over (e.g. SEO was skipped).
    page = seo_page
    if page is None:
        home = safe_get(f"https://{domain}/", timeout)
        if home.ok:
            page = parse_page(home.body)
            schema_types = extract_schema_types(page.jsonld_blocks)
    if schema_types is None:
        schema_types = set()

    # --- AI cite-bot access in robots (25) ---
    robots_res = safe_get(f"https://{domain}/robots.txt", timeout)
    robots_data = parse_robots(robots_res.body) if (robots_res.ok and robots_res.body) else {"agents": {}, "sitemaps": []}
    not_blocked = 0
    bot_status = {}
    for bot in AI_CITE_BOTS:
        blocked = robots_blocks_root(robots_data, bot)
        bot_status[bot] = "blocked" if blocked else "allowed"
        if not blocked:
            not_blocked += 1
    bot_pts = round(25.0 * (not_blocked / len(AI_CITE_BOTS)), 2)
    dim.add("ai_bot_access", Check(
        value=bot_status, points=bot_pts, max=25,
        note=(f"{not_blocked}/{len(AI_CITE_BOTS)} AI cite-bots not blocked in "
              "robots.txt (CCBot excluded from penalty)"),
    ))

    # --- Machine-readable facts (20): /llms.txt OR /rates.md present ---
    llms = safe_get(f"https://{domain}/llms.txt", timeout)
    rates = safe_get(f"https://{domain}/rates.md", timeout)
    llms_ok = bool(llms.ok and llms.body.strip())
    rates_ok = bool(rates.ok and rates.body.strip())
    facts_pts = 20.0 if (llms_ok or rates_ok) else 0.0
    dim.add("machine_readable_facts", Check(
        value={"llms_txt": llms_ok, "rates_md": rates_ok},
        points=facts_pts, max=20,
        note="/llms.txt or /rates.md present",
    ))

    # --- AI-relevant schema (20) ---
    relevant = sorted(t for t in schema_types if t in AI_RELEVANT_SCHEMA)
    ai_schema_pts = 20.0 if relevant else 0.0
    dim.add("ai_relevant_schema", Check(
        value=relevant, points=ai_schema_pts, max=20,
        note=("any of FAQPage/HowTo/Article/BlogPosting/Organization/"
              "FinancialProduct/Product/Review/AggregateRating in raw HTML"),
    ))

    # --- Extractable structure (20): good 20 / partial 10 / poor 0 ---
    if page is not None:
        headings = page.h2_count + page.h3_count
        has_list_or_table = (page.list_count >= 1) or (page.table_count >= 1)
        if headings >= 4 and has_list_or_table:
            struct_pts, bucket = 20.0, "good"
        elif headings >= 2:
            struct_pts, bucket = 10.0, "partial"
        else:
            struct_pts, bucket = 0.0, "poor"
        struct_value = {
            "bucket": bucket, "h2_h3": headings,
            "lists": page.list_count, "tables": page.table_count,
        }
    else:
        struct_pts, struct_value = 0.0, {"bucket": "poor", "h2_h3": 0,
                                         "lists": 0, "tables": 0}
    dim.add("extractable_structure", Check(
        value=struct_value, points=struct_pts, max=20,
        note="good (>=4 H2/H3 AND (>=1 list OR table)) 20 / partial (>=2 headings) 10 / poor 0",
    ))

    # --- /llms.txt present (15) ---
    dim.add("llms_txt", Check(
        value=llms_ok, points=(15.0 if llms_ok else 0.0), max=15,
        note="/llms.txt present",
    ))

    # Unscored qualitative note — citation presence is NEVER scored (not reproducible).
    dim.checks["citation_note"] = Check(
        value=("Whether this site is actually cited by ChatGPT/Perplexity/Google AI "
               "is NOT scored here — it isn't reproducible. Use the ai-seo skill to "
               "run a live citation check."),
        points=0.0, max=0,
        note="unscored: AI citation presence is never part of the score",
    )

    return dim


# --- report assembly ---------------------------------------------------------

def overall_status(score: float) -> str:
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Needs work"
    if score >= 30:
        return "Weak"
    return "Critical"


def build_json(domain: str, input_meta: dict, dims: dict,
               skipped: list, warnings: list) -> dict:
    available_scores = [d.score() for d in dims.values()
                        if d.available and d.score() is not None]
    overall = round(sum(available_scores) / len(available_scores), 1) if available_scores else None
    return {
        "schema_version": SCHEMA_VERSION,
        "score_version": SCORE_VERSION,
        "generated_at": date.today().isoformat(),
        "input": input_meta,
        "overall_score": overall,
        "dimensions": {name: d.as_dict() for name, d in dims.items()},
        "skipped": skipped,
        "warnings": warnings,
    }


def _score_cell(score: Optional[float]) -> str:
    if score is None:
        return "— (skipped)"
    return f"{score:.1f} — {overall_status(score)}"


def build_markdown(report: dict, domain: str) -> str:
    """Build the LLM-narrative-ready Markdown. FIRST LINE is a single H1 so
    growgami-pdf turns it into the cover and strips it from the body."""
    dims = report["dimensions"]
    overall = report["overall_score"]
    lines: list[str] = []
    lines.append(f"# Growth Scorecard — {domain}")
    lines.append("")
    if overall is not None:
        lines.append(f"> **Overall Growth Score: {overall:.1f} / 100 — {overall_status(overall)}**")
    else:
        lines.append("> **Overall Growth Score: not available — no dimensions could be scored.**")
    lines.append("")
    lines.append("<!-- NARRATIVE: one-paragraph executive summary of the score and the single biggest growth lever. -->")
    lines.append("")

    # Scores at a glance.
    lines.append("## Scores at a glance")
    lines.append("")
    lines.append("| Dimension | Score | Status |")
    lines.append("| --- | --- | --- |")
    label = {"seo": "SEO", "aso": "ASO (Apple)", "ai_seo": "AI-SEO readiness"}
    for key in ("seo", "aso", "ai_seo"):
        d = dims.get(key, {})
        lines.append(f"| {label[key]} | {_score_cell(d.get('score'))} |"
                     f" {overall_status(d['score']) if d.get('score') is not None else 'skipped'} |")
    lines.append(f"| **Overall (mean of available)** | **{overall:.1f}** | **{overall_status(overall)}** |"
                 if overall is not None else "| **Overall** | **—** | **n/a** |")
    lines.append("")

    # Per-dimension detail tables.
    for key in ("seo", "aso", "ai_seo"):
        d = dims.get(key)
        if not d:
            continue
        lines.append(f"## {label[key]}")
        lines.append("")
        if d.get("score") is None:
            lines.append(f"_Skipped — see caveats below._")
            lines.append("")
            continue
        lines.append(f"**Dimension score: {d['score']:.1f} / 100 — {overall_status(d['score'])}**")
        lines.append("")
        lines.append(f"<!-- NARRATIVE: interpret the {label[key]} checks below and give the top 2-3 fixes. -->")
        lines.append("")
        lines.append("| Check | Points | Max | Detail |")
        lines.append("| --- | --- | --- | --- |")
        for ckey, chk in d["checks"].items():
            if chk["max"] == 0 and ckey == "citation_note":
                continue
            note = str(chk["note"]).replace("|", "\\|")
            lines.append(f"| {ckey} | {chk['points']} | {chk['max']} | {note} |")
        lines.append("")
        # Surface the unscored citation note as prose, not a scored row.
        if key == "ai_seo" and "citation_note" in d["checks"]:
            cnote = str(d["checks"]["citation_note"]["value"]).replace("|", "\\|")
            lines.append(f"> _Citation note (unscored):_ {cnote}")
            lines.append("")

    # How this score was computed.
    lines.append("## How this score was computed")
    lines.append("")
    lines.append(f"- **Score version:** {report['score_version']} · **Generated:** {report['generated_at']}")
    lines.append("- **Overall** is the simple mean of the dimensions that had checks run.")
    lines.append("- Each dimension normalizes earned points over the max of the checks that "
                 "actually ran (skipped checks drop out and the rest renormalize).")
    lines.append("- **SEO (public HTML + PageSpeed Insights):** Core Web Vitals 28 "
                 "(LCP 12 / INP 8 / CLS 8), raw-HTML content 12, title+meta 12, robots+sitemap 8, "
                 "headings 8, JSON-LD schema 8, HTTPS+redirect 8, viewport 6, `<html lang>` 8.")
    lines.append("- **Core Web Vitals are scored by CrUX category bucket** (FAST=full, "
                 "AVERAGE=half, SLOW=0), never by a raw number — so re-runs are identical. "
                 "Lab data is bucketed against the standard thresholds when field data is absent.")
    lines.append("- **ASO (public Apple iTunes lookup):** rating 25, review-count tier 20, "
                 "title+subtitle 20, screenshots 15, description 10, update freshness 10.")
    lines.append("- **AI-SEO (readiness only):** AI cite-bot access 25, machine-readable facts 20, "
                 "AI-relevant schema 20, extractable structure 20, `/llms.txt` 15. "
                 "Whether an AI actually cites the site is never scored.")
    lines.append("")
    lines.append("<!-- NARRATIVE: optional — restate the methodology in client-friendly terms. -->")
    lines.append("")

    # Skipped & caveats.
    lines.append("## Skipped checks & caveats")
    lines.append("")
    lines.append("- SEO signals are read from **raw HTML only** — JS-injected schema/content is "
                 "not visible here; confirm in a browser.")
    lines.append("- AI **citation presence is not scored** (not reproducible) — only readiness signals are.")
    lines.append("- ASO is **Apple-only in v1**; screenshot/keyword craft is deferred to the `aso` skill.")
    if report["skipped"]:
        for item in report["skipped"]:
            where = item.get("dimension") or item.get("check") or "check"
            lines.append(f"- **Skipped ({where}):** {item.get('reason', '')}")
    if report["warnings"]:
        lines.append("")
        lines.append("**Warnings:**")
        for w in report["warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("<!-- NARRATIVE: optional closing — what to fix first and the expected payoff. -->")
    lines.append("")
    return "\n".join(lines)


# --- CLI ---------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute a reproducible public-data Growth Score (SEO/ASO/AI-SEO).",
    )
    parser.add_argument("domain", help="Target domain, e.g. monzo.com")
    parser.add_argument("--app-store", dest="app_store",
                        help="Apple App Store URL (enables ASO; Apple-only in v1).")
    parser.add_argument("--play-store", dest="play_store",
                        help="Google Play URL (accepted but skipped in v1).")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile",
                        help="PageSpeed Insights strategy (default: mobile).")
    parser.add_argument("-o", "--output",
                        help="Output basename (default: <domain>-growth-scorecard-<date>).")
    parser.add_argument("--json-only", action="store_true", help="Write only the JSON.")
    parser.add_argument("--md-only", action="store_true", help="Write only the Markdown.")
    parser.add_argument("--no-cwv", action="store_true", help="Skip Core Web Vitals.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    args = parser.parse_args()

    domain = normalize_domain(args.domain)
    if domain is None:
        print(f"error: invalid domain: {args.domain!r}\n"
              "Provide a bare hostname like 'monzo.com' (no scheme/path, no IP).",
              file=sys.stderr)
        return 1

    timeout = args.timeout if args.timeout and args.timeout > 0 else DEFAULT_TIMEOUT
    warnings: list = []
    skipped: list = []

    # Play Store is accepted but never scraped in v1.
    if args.play_store:
        skipped.append({"dimension": "play_store", "reason": "Play not supported in v1"})

    dims: dict[str, Dimension] = {}
    seo_page: Optional[_PageParser] = None
    seo_schema: Optional[set] = None

    # --- SEO ---
    try:
        seo_dim = score_seo(domain, timeout, do_cwv=not args.no_cwv,
                            strategy=args.strategy, warnings=warnings, skipped=skipped)
        dims["seo"] = seo_dim
        # Reuse the homepage parse for AI-SEO if SEO fetched it.
        if seo_dim.available:
            home = safe_get(f"https://{domain}/", timeout)
            if home.ok:
                seo_page = parse_page(home.body)
                seo_schema = extract_schema_types(seo_page.jsonld_blocks)
    except Exception as exc:
        dims["seo"] = Dimension("seo", available=False, skip_reason=f"SEO failed: {exc}")
        skipped.append({"dimension": "seo", "reason": f"unexpected failure: {exc}"})

    # --- ASO (Apple-only) ---
    if args.app_store:
        try:
            dims["aso"] = score_aso(args.app_store, timeout, warnings, skipped)
        except Exception as exc:
            dims["aso"] = Dimension("aso", available=False, skip_reason=f"ASO failed: {exc}")
            skipped.append({"dimension": "aso", "reason": f"unexpected failure: {exc}"})
    else:
        d = Dimension("aso", available=False, skip_reason="no --app-store URL provided")
        dims["aso"] = d
        skipped.append({"dimension": "aso", "reason": "no --app-store URL provided"})

    # --- AI-SEO ---
    try:
        dims["ai_seo"] = score_ai_seo(domain, timeout, seo_page, seo_schema,
                                      warnings, skipped)
    except Exception as exc:
        dims["ai_seo"] = Dimension("ai_seo", available=False, skip_reason=f"AI-SEO failed: {exc}")
        skipped.append({"dimension": "ai_seo", "reason": f"unexpected failure: {exc}"})

    # If a whole dimension blew up unexpectedly (vs. a graceful skip), exit 2.
    unexpected = [s for s in skipped if "unexpected failure" in str(s.get("reason", ""))]

    input_meta = {
        "domain": domain,
        "app_store": args.app_store or None,
        "play_store": args.play_store or None,
        "strategy": args.strategy,
        "cwv": not args.no_cwv,
    }
    report = build_json(domain, input_meta, dims, skipped, warnings)

    # Exit 1 if literally no checks ran anywhere.
    any_checks = any(
        any(c.max > 0 for c in d.checks.values()) for d in dims.values()
    )
    if not any_checks:
        print("error: no checks could be run (target unreachable?).", file=sys.stderr)
        return 1

    basename = args.output or f"{domain}-growth-scorecard-{date.today().isoformat()}"
    # Strip a trailing .json/.md if the caller passed a filename.
    basename = re.sub(r"\.(json|md)$", "", basename)

    if not args.md_only:
        json_path = f"{basename}.json"
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"Wrote {json_path}")
    if not args.json_only:
        md_path = f"{basename}.md"
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(build_markdown(report, domain))
        print(f"Wrote {md_path}")

    if report["overall_score"] is not None:
        print(f"Overall Growth Score: {report['overall_score']} "
              f"({overall_status(report['overall_score'])})")

    if unexpected:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
