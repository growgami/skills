# Competitor Reviews — <Target> vs. Top Competitors

<!--
TIGHT, SCANNABLE skeleton for the neobank-competitor-reviews skill.
- Target: 4–6 pages. Favor tables and bullets over paragraphs. No paragraph
  longer than ~3 lines. One attributed quote per competitor MAX.
- Keep the SINGLE leading `# H1` above so growgami-pdf can use it as the cover
  and strip it from the body. Do not add a second H1.
- Replace every <placeholder>. Delete rows/sections that don't apply.
- Every score must show its confidence flag (High / Med / Low) beside it.
- SINGLE-STORE IS THE NORM, not a failure. Google Play data is frequently
  absent (JS-rendered). When a store is missing, just say so in the short
  score parenthetical — the score weights/confidence already handle it.
-->

> Composite scores are 0–100 (volume-weighted store ratings + an LLM sentiment
> read). Confidence flags how much real signal backed each score. Sentiment is a
> qualitative model read, not a statistical study. See Methodology.
>
> **Target:** <Target> · **Segment/region:** <...> · **Generated:** <YYYY-MM-DD>
> · **Sources:** App Store, Google Play, Reddit, YouTube, Google (web tools only)

## Executive summary

<3–4 sentences MAX. Lead with the ranking (top + bottom) and the single
cross-competitor insight (the dominant shared pain point and where <Target> has
an opening). Name any top-5 placement that rests on Low confidence.>

## Ranked top 5

| Rank | Competitor | Score (0–100) | Confidence | One-line read |
| --- | --- | --- | --- | --- |
| 1 | <name> | <score> | High/Med/Low | <e.g. "loved app, support gripes"> |
| 2 | <name> | <score> | High/Med/Low | <...> |
| 3 | <name> | <score> | High/Med/Low | <...> |
| 4 | <name> | <score> | High/Med/Low | <...> |
| 5 | <name> | <score> | High/Med/Low | <...> |

<!-- If a Low-confidence score outranks a High-confidence one, add one caveat
line here, e.g. "Note: #2 ranks on score but is Low confidence (thin sample)." -->

## Pain-point themes (across the field)

One tight line per theme — theme, then who it hits.

- **<Theme, e.g. Frozen accounts / sudden closures>** — <competitors>.
- **<Theme, e.g. Support unreachable / slow>** — <competitors>.
- **<Theme, e.g. Transfer / deposit delays>** — <competitors>.
- **<Theme, e.g. Hidden / surprise fees>** — <competitors>.
- **<Theme, e.g. App instability / outages>** — <competitors>.

---

## Per-competitor detail

<!-- Compact card per top-5 competitor. ONE quote max. No score-math paragraph
(use the short parenthetical). No "Data gaps" prose (use the Coverage half-line
or drop it). -->

### <Rank>. <Competitor> — <score>/100 · <Confidence>

(App Store <x.x>/<N>, Google Play <x.x>/<N> or "not available", sentiment <±n>)

- **Liked:** <one line.>
- **Top pain points:**
  - <pain point> — <source link>
  - <pain point> — <source link>
  - <pain point> — <source link>
- <!-- ONE attributed quote. Frame as a user claim, never a stated fact about
  the company (defamation safety): "a user reported…", "according to a
  reviewer…", "one Redditor claimed…". -->
  > "<short representative review>" — a user reported, <source, link>
- **Coverage:** <half-line: missing store / Reddit via roundups / category nuance.>

---

## Methodology & confidence

- **Sources (v1, web tools only):** App Store + Google Play, Reddit, YouTube,
  Google (Trustpilot/BBB/G2/etc.). Built-in WebSearch / WebFetch — no APIs or keys.
- **Scoring:** composite 0–100 = volume-weighted star base + capped (±12)
  cross-source LLM sentiment read. Full rubric in `references/scoring-rubric.md`.
- **Sentiment is an LLM read,** not a statistical study; **store numbers are
  best-effort** (stale/regional/rounded, read <YYYY-MM-DD>); Google Play is often
  JS-rendered/absent — expected, handled by weighting + confidence, not a failure.
- **Quote attribution:** every quote is a user claim/allegation, not a verified fact.
- **Low-confidence competitors:** <list any, with why — or "none">. **X/Twitter deferred to v2.**

## Sources

<!-- Links only, grouped under competitor names. Keep it auditable + re-runnable. -->

**<Competitor>** — <url> · <url> · <url>
**<Competitor>** — <url> · <url> · <url>
