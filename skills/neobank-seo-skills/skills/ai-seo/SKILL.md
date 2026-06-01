---
name: ai-seo
description: "When the user wants a neobank or fintech brand cited by AI search engines and answer engines. Also use for 'AI SEO,' 'AEO,' 'GEO,' 'answer engine optimization,' 'generative engine optimization,' 'AI Overviews,' 'optimize for ChatGPT/Perplexity/Gemini/Claude,' 'AI citations,' 'AI visibility,' 'zero-click,' or 'how do I show up in AI answers.' For traditional SEO see seo-audit; for structured data see schema."
metadata:
  version: 2.0.1-neobank
---

<!-- Adapted from coreyhaines31/marketingskills `ai-seo` (MIT). The landscape, Princeton GEO findings, three-pillar model, bot-access checks, machine-readable files, monitoring tools, and "what not to do" are retained; neobank additions are the YMYL framing, query set, third-party sources, the rates/fees freshness emphasis, and the structured-facts file. -->

# AI SEO (AEO / GEO) — Neobank / Fintech

Traditional SEO gets you **ranked**; AI SEO gets you **cited** — surfaced as a source when someone asks ChatGPT, Perplexity, Gemini, Claude, Copilot, or Google AI Overviews a question. For a neobank this matters twice over: (1) fintech buyers increasingly research "best bank for X" and "is X safe" through assistants, and (2) being cited with a *stale* fee or APY is worse than not being cited — so freshness is a first-class concern, treated here as accuracy hygiene, not legal compliance.

Read `.agents/product-marketing.md` first; gather current AI visibility, content/domain strength, goals, and which competitors get cited where you don't.

## How AI search works

| Platform | Source selection |
|---|---|
| Google AI Overviews / AI Mode | Strongly tied to traditional rankings + E-E-A-T |
| ChatGPT (search) | Wider range, rewards extractable structure |
| Perplexity | Authoritative, recent, well-structured; always cites |
| Gemini | Google index + Knowledge Graph |
| Copilot | Bing index |

Key context: AI Overviews appear in ~45% of Google searches and can cut clicks by up to ~58%; brands are far more likely to be cited via **third-party** sources than their own domain; optimized, stat-backed content is cited several times more often.

**Google's official stance:** no special markup or "AI files" needed; write for people; *don't* write separate content for AI or chunk pages into fragments (risks the scaled-content-abuse policy); same E-E-A-T standards as Search. **Other engines** (ChatGPT/Perplexity/Claude) actively reward extractable structure and machine-readable files and lean on third-party sources. Default: write for people, organize for clarity — that satisfies both.

**Query fan-out:** Google generates related sub-queries under the hood, so cover the full topical cluster, not one page per keyword.

## AI visibility audit
Test 10–20 priority queries across Google AIO / ChatGPT / Perplexity and log: are you cited, who is? For a neobank the query set is:
- "what is a neobank / digital bank"
- "best bank account for [freelancers / teens / no-SSN / bad credit / immigrants]"
- "[brand] vs [Chime / Cash App / competitor]"
- "is [brand] safe / legit / FDIC insured"
- "how to [get paid early / send money to X / avoid bank fees]"
- "[brand] fees / does [brand] charge"

When a competitor is cited and you aren't, examine structure, authority signals (stats, expert quotes), freshness, schema, and third-party presence.

**AI bot access:** check robots.txt isn't blocking GPTBot, ChatGPT-User, PerplexityBot, ClaudeBot/anthropic-ai, Google-Extended, Bingbot — blocking them means those engines literally can't cite you. (You can block training-only crawlers like CCBot while allowing search/cite bots.)

## Optimization — three pillars

**1. Structure (make it extractable).** AI extracts passages, not pages. Lead each section with a direct answer; keep key answer blocks ~40–60 words; H2/H3 phrased like real queries; tables for "X vs Y," numbered lists for "how to." Use definition / step / comparison / pros-cons / FAQ / statistic blocks.

**2. Authority (make it citable).** Per the Princeton GEO study, the biggest visibility boosts come from **citing sources (+40%)**, **statistics (+37%)**, **quotations (+30%)**, and an **authoritative tone (+25%)** — while **keyword stuffing actively hurts (−10%)**. For a YMYL bank this aligns exactly with E-E-A-T: named authors with finance credentials, sourced claims, original data ("our users set up direct deposit in X minutes"), and prominent "last updated" dates. Fluency + statistics is the strongest combination.

**3. Presence (be where AI looks).** AI cites third parties more than your own site. For fintech that means: Wikipedia (accurate, current), Reddit (r/personalfinance and authentic participation), reputable roundups and "best neobank" comparisons, App Store/Trustpilot reviews, and YouTube how-tos. Earn genuine mentions; never fabricate or spam them.

## Machine-readable facts file (the fintech version of /pricing.md)
AI agents increasingly compare products before a human visits. Put your **rates, fees, eligibility, and supported regions** in a clean, public, parseable page (and/or a `/rates.md` + `/llms.txt`) — not locked behind JS or "see app." Keep it current from a single source of truth; a stale file is worse than none. This is how an assistant quotes *your* accurate numbers instead of a third party's outdated ones.

## Schema for AI
`Article`/`BlogPosting`, `FAQPage`, `HowTo`, `FinancialProduct`/`Product`, `Organization`, `Review`/`AggregateRating`. Helps non-Google engines materially; recommended (not required) for Google. Implement via the `schema` skill — keep marked-up rates/fees matching the visible page.

## Monitoring
No AI-specific Search Console report exists; use standard GSC + GA4 for Google, and cross-platform AI-visibility tools for the rest: **Peec AI**, **Otterly AI**, **ZipTie**, **LLMrefs** (share-of-voice, citations, sentiment). At minimum, run the 20-query manual check monthly and track month-over-month.

## What NOT to do
Write separate "AI content"; chunk pages into fragments; mass-generate thin variations; fabricate mentions; block the cite bots; hide content (or rates) behind un-rendered JS; skip E-E-A-T; leave content undated.

## Related skills
`seo-audit` · `schema` · `programmatic-seo` · `competitor-pages`
