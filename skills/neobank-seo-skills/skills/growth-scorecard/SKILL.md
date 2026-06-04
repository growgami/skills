---
name: growth-scorecard
description: When the user wants a reproducible, public-data Growth Score for a neobank/fintech across SEO, ASO, and AI-SEO. Triggers on "growth scorecard," "growth score," "score my site," "benchmark growth," "core web vitals score," "reproducible audit," or "automated first-pass before a full seo-audit." Produces a deterministic JSON + a growgami-pdf-ready Markdown report; the LLM writes narrative on top of the fixed score.
metadata:
  version: 1.0.0-neobank
---

# Growth Scorecard — Neobank / Fintech

Compute an objective, **reproducible** Growth Score for a target from **public
data only**. The score is deterministic: a third party running this on the same
target with the same `score_version` gets the same number. The agent then writes
the narrative and recommendations *on top of* the fixed score — it never invents
the number.

This is the engine behind a branded teardown: run it, reproduce the score, and
hand the Markdown to `growgami-pdf` for the client-facing deliverable.

## What it scores (3 dimensions, simple-mean overall)

- **SEO** (max 100) — Core Web Vitals 28 (LCP 12 / INP 8 / CLS 8), raw-HTML/SSR
  content 12, title+meta 12, robots+sitemap 8, headings 8, JSON-LD schema 8,
  HTTPS+redirect 8, viewport 6, `<html lang>` 8.
- **ASO** (max 100, **Apple-only in v1**) — rating 25, review-count tier 20,
  title+subtitle 20, screenshots 15, description 10, update freshness 10.
- **AI-SEO** (max 100, **readiness only**) — AI cite-bot access 25,
  machine-readable facts 20, AI-relevant schema 20, extractable structure 20,
  `/llms.txt` 15.

**Overall = the simple mean of the dimensions that had checks run.** Skipped
checks drop out and the rest renormalize. Full weights and bands:
`references/scoring-rubric.md`.

## The reproducibility promise — and how

The score is computed by the script from public data, not by the model, so it is
**stable across re-runs**:

- **CrUX-banded Core Web Vitals.** CWV is scored by **category bucket**
  (FAST = full, AVERAGE = half, SLOW = 0), never by a raw millisecond/score
  number — so Lighthouse lab jitter can never move the score. CrUX field data is
  preferred; lab data is the fallback, bucketed against the standard thresholds.
- **stdlib only.** The script declares `dependencies = []` (PEP-723), so it runs
  identically via `uv run` and plain `python` — no install drift.
- **public data only.** Homepage HTML, robots.txt, sitemap, PageSpeed Insights,
  and the Apple iTunes Lookup API. Every response is treated as untrusted data:
  parsed with `html.parser` (no JS) and `json.loads` (never eval/exec), and no
  fetched value ever reaches a shell.

## CLI examples

```bash
# Full scorecard: SEO + ASO (Apple) + AI-SEO, JSON + Markdown
uv run scripts/scorecard.py monzo.com \
  --app-store "https://apps.apple.com/gb/app/monzo-bank/id1052238659"

# Just the SEO health JSON, custom basename (used by seo-audit Stage 6)
uv run scripts/scorecard.py monzo.com --json-only -o web-health

# Desktop CWV, skip Core Web Vitals, or raise the timeout
uv run scripts/scorecard.py monzo.com --strategy desktop
uv run scripts/scorecard.py monzo.com --no-cwv
uv run scripts/scorecard.py monzo.com --timeout 20
```

| Flag | Purpose |
| --- | --- |
| `domain` | Target domain, e.g. `monzo.com` (positional). |
| `--app-store` | Apple App Store URL — enables the ASO dimension. |
| `--play-store` | Accepted but **skipped in v1** ("Play not supported in v1"). |
| `--strategy {mobile,desktop}` | PageSpeed Insights strategy (default `mobile`). |
| `-o, --output` | Output basename (default `<domain>-growth-scorecard-<date>`). |
| `--json-only` / `--md-only` | Write only the JSON / only the Markdown. |
| `--no-cwv` | Skip Core Web Vitals. |
| `--timeout` | Per-request timeout in seconds (default 12). |

Set `GROWGAMI_PSI_KEY` for higher PageSpeed Insights rate limits; without it,
keyless PSI is rate-limited and CWV may be gracefully skipped.

## Outputs

- **`<basename>.json`** — the deterministic record:
  `schema_version`, `score_version`, `generated_at`, `input`, `overall_score`,
  `dimensions` (each with `score`, `available`, and per-check
  `{value, points, max, note}`), `skipped[]`, `warnings[]`.
- **`<basename>.md`** — the report skeleton. Its **first line is a single
  `# Growth Scorecard — <domain>`** (growgami-pdf turns the leading H1 into the
  cover and strips it from the body). It includes a one-line overall-score
  blockquote, a "Scores at a glance" table, per-dimension tables (one row per
  check), `<!-- NARRATIVE: ... -->` placeholders where you write the prose, a
  "How this score was computed" section, and a "Skipped checks & caveats"
  section.

Write findings and recommendations into the `<!-- NARRATIVE -->` slots. The JSON
score is fixed; the prose is the taste layer.

## Hand-off to growgami-pdf

Once the Markdown narrative is filled in and proofread, render the branded PDF:

```bash
uv run ../growgami-pdf/scripts/render_pdf.py <md> --client "<Client>"
```

(If `growgami-pdf` was installed separately, point at its
`scripts/render_pdf.py`.) The Markdown stays the re-runnable source of truth; the
PDF is the client-facing copy.

## Graceful degradation

Any single check or whole dimension that fails is **skipped with a recorded
reason** and the run continues — it never crashes. Exit codes: `0` success (even
with skipped checks), `1` invalid domain or no checks ran, `2` a whole dimension
failed unexpectedly.

## Honesty box

- **Raw-HTML only.** SEO/AI-SEO signals are read from raw HTML — JS-injected
  schema or content is not visible here; confirm in a browser.
- **Citations are not scored.** Whether an AI engine actually cites the site is
  not reproducible and is never part of the score (see the unscored
  `citation_note`). Use the `ai-seo` skill for a live citation check.
- **Apple-only ASO in v1.** Google Play is accepted but not scraped.
- **Screenshot quality deferred.** ASO scores screenshot *count* only; keyword
  and creative craft are the `aso` skill's job.

## References
- `references/scoring-rubric.md` — every weight and band, matching the code.

## Related skills
`seo-audit` · `aso` · `ai-seo` · `growgami-pdf`
