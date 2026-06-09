# Scoring Rubric — Composite 0–100 + Confidence Flag

This is the transparent "how the score was built" reference. Unlike
`growth-scorecard`, this score is **not deterministic** — sentiment is an LLM
read. The rubric exists to make every number **explainable in the report**: a
reader should be able to see the base, the adjustment, the final, and why.

The composite has three parts: a **star base (0–100)**, a **sentiment
adjustment (±)**, and a **confidence flag (High / Med / Low)** that always
travels with the score.

---

## Step 1 — Star base (0–100), volume-weighted

Use the App Store and Google Play **star ratings**, weighted by each store's
**approximate review/rating volume**.

**Volume-weighted rating** (5-point scale):

```
weighted_stars = (apple_stars × apple_volume + play_stars × play_volume)
                 / (apple_volume + play_volume)
```

- Use whatever volume figures you have (ratings count preferred; if only a
  downloads tier is visible, use the listed count as a rough weight and note it).
- If only **one** store has data, use that store's rating (and the single-source
  fact lowers confidence in Step 3).
- If **neither** store has a usable rating, there is no star base — score from
  sentiment alone and flag **Low** confidence.

**Map weighted stars → 0–100 base** (linear on the meaningful 1–5 band):

```
star_base = round((weighted_stars - 1) / 4 × 100)
```

| Weighted stars | Star base |
| --- | --- |
| 5.0 | 100 |
| 4.5 | 88 |
| 4.0 | 75 |
| 3.5 | 63 |
| 3.0 | 50 |
| 2.5 | 38 |
| 2.0 | 25 |
| ≤ 1.0 | 0 |

---

## Step 2 — Sentiment adjustment (±, capped)

Read the **qualitative tone** across the non-store sources (Reddit, YouTube,
general Google) **and** the substance of the review text — not just the star
number. Apply a single adjustment to the star base, **capped at ±12 points** so
sentiment refines the verdict but never overrides the actual ratings.

| Cross-source sentiment | Adjustment |
| --- | --- |
| Strongly positive, consistent across sources | +8 to +12 |
| Mildly positive / mixed-leaning-good | +1 to +7 |
| Genuinely mixed | 0 |
| Mildly negative / mixed-leaning-bad | −1 to −7 |
| Strongly negative, recurring serious complaints (frozen funds, no support) | −8 to −12 |

`composite = clamp(star_base + sentiment_adjustment, 0, 100)`

Record the adjustment **with a one-line reason** (e.g. "−9: Reddit and outage
articles dominated by frozen-account complaints despite a 4.2 store rating").
Serious, recurring trust complaints (sudden account closures, withheld funds,
unreachable support) justify the bottom of the range even against decent stars.

---

## Step 3 — Confidence / coverage flag

The flag describes **how much real signal** backed the score — so a thin sample
never reads as a confident verdict. Base it on **(a)** how many sources returned
real signal and **(b)** how substantial the review volume was.

| Flag | Rule |
| --- | --- |
| **High** | ≥ 2 sources with real signal **and** substantial store volume (roughly ≥ 1,000 combined ratings) **and** no major contradictions between sources. |
| **Med** | Some real signal but limited — e.g. 1 store + 1 other source, or moderate volume (~100–1,000 ratings), or sources partly disagree. |
| **Low** | Single thin source, very low volume (< ~100 ratings), mostly JS-rendered/paywalled gaps, or store data missing entirely. |

The flag is **mandatory** and appears beside the score everywhere: the ranked
table, the per-competitor section, and the executive summary.

**Ranking rule:** rank by composite, but **a Low-confidence score must not
silently outrank a High-confidence one.** When that happens, keep the order but
add an explicit caveat in the row/section (e.g. "ranked #2 on score but Low
confidence — thin sample").

---

## Status bands (for narrative)

| Composite | Read |
| --- | --- |
| 85–100 | Loved |
| 70–84 | Well-liked |
| 50–69 | Mixed |
| 30–49 | Struggling |
| < 30 | Poorly received |

---

## Worked example

Competitor X: App Store 4.3 over ~20,000 ratings (US), Google Play 4.1 over
~50,000 ratings.

- weighted_stars = (4.3×20000 + 4.1×50000) / 70000 = **4.16**
- star_base = (4.16 − 1) / 4 × 100 = **79**
- Sentiment: Reddit + YouTube broadly positive, recurring "support slow" gripe →
  adjustment **−3** ("good app, support is the consistent complaint").
- composite = 79 − 3 = **76** → band "Well-liked".
- Confidence: 2 stores + Reddit + YouTube, ~70k ratings, no contradictions →
  **High**.

Report row: `X · 76 · High`, breakdown shown: base 79, adj −3, "support slow".
