# Growth Scorecard — Scoring Rubric (`score_version: 1`)

This is the public "verify the score" reference. Every weight and band below
matches `scripts/scorecard.py` exactly. Anyone re-running the skill on the same
target with the same `score_version` gets the same number.

## How the overall score works

- Each **dimension** (SEO, ASO, AI-SEO) is scored **0–100**.
- A dimension normalizes **earned points ÷ the max of the checks that actually
  ran**. Checks that are skipped (e.g. Core Web Vitals when PageSpeed Insights
  is rate-limited) **drop out and the remaining checks renormalize** — they are
  not counted as zeros.
- **Overall = the simple mean of the dimensions that had any checks run.** A
  dimension with no checks (e.g. ASO with no `--app-store` URL) is excluded from
  the mean entirely.

### Overall / dimension status bands

| Score | Status |
| --- | --- |
| 85–100 | Strong |
| 70–84 | Good |
| 50–69 | Needs work |
| 30–49 | Weak |
| < 30 | Critical |

---

## SEO (public HTML + PageSpeed Insights)

Read from **raw HTML only** (no JavaScript executed), plus PageSpeed Insights
for Core Web Vitals. JS-injected schema/content is not visible here — confirm in
a browser.

| Check | Max | How points are earned |
| --- | --- | --- |
| Core Web Vitals | 28 | LCP 12 / INP 8 / CLS 8, by CrUX category bucket (see below). |
| Raw-HTML / SSR content | 12 | ≥250 words in raw HTML → full; below that, prorated to 250. |
| Title + meta description | 12 | 6 — title present & 15–60 chars · 6 — meta present & 50–160 chars. |
| robots.txt + sitemap | 8 | 4 — robots.txt reachable & no blanket `Disallow: /` · 4 — sitemap returns XML. |
| Headings | 8 | 5 — exactly one raw `<h1>` · 3 — at least one `<h2>`. |
| JSON-LD schema present | 8 | Full if any JSON-LD block parses in raw HTML. |
| HTTPS + redirect | 8 | 4 — HTTPS serves the homepage · 4 — HTTP redirects to HTTPS. |
| Viewport | 6 | Full if a `width=`-bearing viewport meta is present. |
| `<html lang>` | 8 | Full if the `<html>` tag carries a `lang` attribute (≥2 chars). |

**SEO total max:** 100 (28 + 12 + 12 + 8 + 8 + 8 + 8 + 6 + 8).

### Core Web Vitals — the reproducibility crux

CWV is **always scored by category bucket, never by a raw number**, so lab-run
jitter can never move the score.

1. **Prefer CrUX field data** (`loadingExperience`, falling back to
   `originLoadingExperience`). Each metric carries a `category`:
   - `FAST` → full points · `AVERAGE` → half points · `SLOW` (or missing) → 0.
   - `cwv_source: "field"`.
2. **If there is no field data**, fall back to Lighthouse **lab** `numericValue`
   and bucket it against the standard thresholds, then score the bucket the same
   way. `cwv_source: "lab"` plus a warning.

| Metric | FAST (full) | AVERAGE (half) | SLOW (0) | Points |
| --- | --- | --- | --- | --- |
| LCP | ≤ 2.5 s | 2.5–4.0 s | ≥ 4.0 s | 12 |
| INP | ≤ 200 ms | 200–500 ms | ≥ 500 ms | 8 |
| CLS | ≤ 0.1 | 0.1–0.25 | ≥ 0.25 | 8 |

If PageSpeed Insights returns a non-200 or 429, the script retries once after a
2-second backoff, then **skips CWV** (SEO renormalizes over the remaining 72
points) and adds a warning suggesting the `PAGESPEED_API_KEY` environment
variable for higher rate limits.

---

## ASO (Apple App Store — Apple-only in v1)

Read from the public Apple iTunes Lookup API
(`https://itunes.apple.com/lookup?id=<id>&country=<cc>`). The app id and country
are parsed from the `--app-store` URL; a bare name uses the search endpoint, and
an id that returns no result falls back to a name search from the URL slug.

**Google Play is accepted (`--play-store`) but never scraped in v1** — it is
recorded as skipped with the reason "Play not supported in v1".

| Check | Max | Bands |
| --- | --- | --- |
| Rating | 25 | ≥4.5 → 25 · 4.0–4.49 → 18 · 3.5–3.99 → 10 · <3.5 → 0. (Rating rounded to 0.1 first.) |
| Review-count tier | 20 | ≥100k → 20 · 10k–100k → 15 · 1k–10k → 10 · <1k → 4. |
| Title + subtitle | 20 | 10 — title non-empty & ≤30 chars · 10 — subtitle present & ≤30 chars. |
| Screenshots | 15 | ≥5 → 15 · 3–4 → 9 · <3 → 0. (iPhone + iPad counts combined; quality craft is deferred to the `aso` skill.) When **both** screenshot arrays come back empty/absent the Apple API simply isn't exposing them (a published app can't have zero), so the check is **skipped and ASO renormalizes** rather than scoring 0/15. |
| Description | 10 | ≥500 chars → 10 · ≥100 → 5 · else 0. |
| Update freshness | 10 | ≤30d → 10 · ≤90d → 7 · ≤180d → 3 · older → 0. |

**ASO total max:** 100. (The iTunes Lookup API may not expose a subtitle; when
absent, the subtitle half scores 0. When the API exposes no screenshots, the
screenshots check drops out and ASO renormalizes over the remaining checks.)

---

## AI-SEO (readiness only)

Measures whether the site is **ready** to be cited by answer engines. It
**never** scores whether the site is actually cited by ChatGPT/Perplexity/Google
AI — that is not reproducible, and is surfaced only as an unscored
`citation_note`.

| Check | Max | How points are earned |
| --- | --- | --- |
| AI cite-bot access | 25 | Fraction of {GPTBot, ChatGPT-User, PerplexityBot, ClaudeBot, anthropic-ai, Google-Extended, Bingbot} **not** blocked by a `Disallow: /` in robots.txt, × 25. CCBot is excluded from the penalty. |
| Machine-readable facts | 20 | Full if `/llms.txt` **or** `/rates.md` is present. |
| AI-relevant schema | 20 | Full if any of FAQPage / HowTo / Article / BlogPosting / Organization / FinancialProduct / Product / Review / AggregateRating appears in raw-HTML JSON-LD. |
| Extractable structure | 20 | **good** (≥4 H2/H3 **and** (≥1 list **or** table)) → 20 · **partial** (≥2 headings) → 10 · **poor** → 0. |
| `/llms.txt` present | 15 | Full if `/llms.txt` is reachable. |

**AI-SEO total max:** 100.

`citation_note` is always present, always unscored (max 0): a reminder that live
AI-citation presence is not part of the score — use the `ai-seo` skill for a
live citation check.

---

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success — even if some checks or a whole dimension were gracefully skipped. |
| 1 | Invalid domain, or no checks could be run anywhere. |
| 2 | A whole dimension failed **unexpectedly** (an internal error, not a graceful skip). |
