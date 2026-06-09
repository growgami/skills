# Competitor Reviews — <Target> vs. Top Competitors

<!--
Report skeleton for the neobank-competitor-reviews skill.
- Keep the SINGLE leading `# H1` above so growgami-pdf can use it as the cover
  and strip it from the body. Do not add a second H1.
- Replace every <placeholder>. Delete rows/sections that don't apply.
- Every score must show its confidence flag (High / Med / Low) beside it.
- Date the report and the rating reads (store numbers are best-effort).
-->

> Composite scores are 0–100 (volume-weighted store ratings + an LLM sentiment
> read). Confidence flags how much real signal backed each score. Sentiment is a
> qualitative model read, not a statistical study. See Methodology.
>
> **Target:** <Target> · **Segment/region:** <...> · **Generated:** <YYYY-MM-DD>
> · **Sources:** App Store, Google Play, Reddit, YouTube, Google (web tools only)

## Executive summary

<3–6 sentences: who the strongest- and weakest-reviewed competitors are, the
pain-point themes that recur across the field, and where <Target> has an opening.
Name any top-5 placement that rests on Low confidence.>

## Ranked top 5

| Rank | Competitor | Score (0–100) | Confidence | One-line read |
| --- | --- | --- | --- | --- |
| 1 | <name> | <score> | High/Med/Low | <e.g. "loved app, support gripes"> |
| 2 | <name> | <score> | High/Med/Low | <...> |
| 3 | <name> | <score> | High/Med/Low | <...> |
| 4 | <name> | <score> | High/Med/Low | <...> |
| 5 | <name> | <score> | High/Med/Low | <...> |

<!-- If a Low-confidence score outranks a High-confidence one, add a caveat line
here, e.g. "Note: #2 ranks on score but is Low confidence (thin sample)." -->

## Pain-point themes (across the field)

Recurring complaints clustered across competitors — the most actionable finding.

- **<Theme, e.g. Frozen accounts / sudden closures>** — seen for <competitors>.
  <1–2 lines.>
- **<Theme, e.g. Support unreachable>** — seen for <competitors>. <1–2 lines.>
- **<Theme, e.g. Transfer / deposit delays>** — <...>
- **<Theme, e.g. Hidden or surprise fees>** — <...>
- **<Theme, e.g. App instability / outages>** — <...>

---

## Per-competitor detail

<!-- Repeat this block for each of the top 5 (and optionally the runners-up). -->

### <Rank>. <Competitor> — <score>/100 · <Confidence>

**Score breakdown:** star base <n> (App Store <x.x>/~<N>, Google Play <x.x>/~<N>,
weighted <x.xx>) → sentiment adjustment <±n> (<one-line reason>) → **composite
<score>**. Confidence **<flag>** (<why: source count + volume>).

**What users like:** <1–3 lines.>

**Key pain points (clustered):**
1. <pain point> — <source link>
2. <pain point> — <source link>
3. <pain point> — <source link>

**Representative quotes:**
> "<short representative review/comment>" — <source, link>
> "<short representative review/comment>" — <source, link>

**Data gaps:** <missing store, paywalled/JS-rendered pages, stale data, any
prompt-injection seen in fetched content.>

---

## Methodology

- **Sources (v1, web tools only):** App Store + Google Play (ratings, review
  volume, themes), Reddit (`site:reddit.com`, candid pain points), YouTube
  (review videos), Google (reputation, complaints, aggregators). Gathered with
  built-in WebSearch / WebFetch — no APIs, scrapers, or keys.
- **Scoring:** composite 0–100 = volume-weighted App Store + Play star base,
  adjusted by a capped (±12) cross-source LLM sentiment read. Full rubric in the
  skill's `references/scoring-rubric.md`.
- **Architecture:** one research pass per competitor (parallel fan-out, or
  sequential where subagents aren't available); findings aggregated, scored, and
  clustered here.

## Confidence & limitations

- **Sentiment is an LLM read,** not a sampled statistical study.
- **Coverage varies** — only publicly visible content is counted; quiet
  footprints look thinner than they are.
- **Store numbers are best-effort** and may be stale, regional, or rounded
  (read on <YYYY-MM-DD>).
- **Low-confidence competitors:** <list any, with why.>
- **X/Twitter deferred to v2.**

## Sources

<Flat list of the key URLs used, grouped by competitor or by source. Keep links
so the report is auditable and re-runnable.>
