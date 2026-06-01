---
name: programmatic-seo
description: When the user wants to build SEO pages at scale for a neobank or fintech site using templates and data. Also use for "programmatic SEO," "pSEO," "template pages," "pages at scale," "location pages," "persona pages," "comparison pages," "[keyword] + [variable] pages," or "generate N pages." For auditing existing pages see seo-audit; for AI citation see ai-seo.
metadata:
  version: 2.0.0-neobank
---

<!-- Adapted from coreyhaines31/marketingskills `programmatic-seo` (MIT). Core principles, the playbook model, implementation framework, and quality checks retained; neobank additions are the data-defensibility reality, the YMYL quality floor, freshness/single-source, and licensed-region constraint. -->

# Programmatic SEO — Neobank / Fintech

Building many template-driven pages from a dataset. It works for neobanks **only with proprietary or product-derived data and a real per-page value floor** — because Google's YMYL bar filters thin, templated financial pages fast. A swapped-variable page about money is exactly what gets suppressed. Quality over quantity is not a slogan here; it's the constraint.

Read `.agents/product-marketing.md` first.

## Initial assessment
Product/audience/conversion goal; the search pattern and how many real combinations exist; and — critically — **who ranks now and whether you can realistically compete** (on most head money terms the answer is the affiliate publishers and no; pick patterns where you can win).

## Core principles
1. **Unique value per page** — not swapped variables; conditional, data-driven content.
2. **Proprietary data wins.** Defensibility: proprietary > product-derived > user-generated > licensed > public. For a neobank your edge is product-derived data (real fees, supported corridors, eligibility, rates) — use it; don't build pages on public data anyone can template.
3. **Subfolders, not subdomains** (consolidates authority).
4. **Genuine intent match.** 5. **Quality over quantity** — 100 great pages beat 10,000 thin ones. 6. **No doorway pages, stuffing, or duplicates.**

## Playbooks that fit neobanks

| Playbook | Pattern | Neobank example | Notes |
|---|---|---|---|
| Personas | "[account] for [audience]" | "bank account for freelancers / teens / no SSN" | The strongest wedge — maps to differentiators |
| Comparisons | "[brand] vs [X]" / "[X] alternatives" | "Acme vs Chime" | High intent; see `competitor-pages` |
| Conversions | "[X] to [Y]" | "send money to [country]", currency/fee calculators | Great if you have a product utility behind it |
| Locations | "[service] in [region]" | state/region pages | **Only where licensed** — never generate geoblocked regions |
| Glossary | "what is [term]" | "what is early direct deposit" | E-E-A-T + AI citation; low direct ROI |
| Curation | "best [category] for [X]" | "best fee-free accounts for students" | Competes with publishers — be honestly useful or skip |

## Implementation framework
1. **Pattern research** — the repeating structure, the variables, real combination count, aggregate demand.
2. **Data** — source per-page data (favor first-party/product-derived); define how it's updated.
3. **Template** — keyword header, *unique* intro, data-driven sections, internal links, intent-appropriate CTA; conditional content so pages genuinely differ.
4. **Internal linking** — hub-and-spoke; no orphans; sitemap; breadcrumbs.
5. **Indexation** — prioritize high-value patterns; noindex thin variations; separate sitemaps by type; manage crawl budget.

## Freshness & single source of truth (the scale trap)
Templated pages multiply *staleness*: one outdated rate/fee becomes hundreds of outdated URLs. Drive all rate/fee/eligibility values from **one source** feeding both visible copy and schema, with visible last-updated dates. This is SEO/accuracy hygiene — whether any number is legally adequate is the client's review, not this skill's.

## Quality checks
Pre-launch: each page has unique value + intent match; unique titles/meta; heading structure; schema; speed; internal links; in sitemap; crawlable; no conflicting noindex.
Post-launch: track indexation rate, rankings, traffic, engagement, conversion (to *funded* accounts, not sessions). Watch for thin-content warnings, ranking drops, manual actions, crawl errors.

## Common mistakes
Thin "swap the city" pages; cannibalization; generating pages with no demand; outdated data; pages built for Google not users; building on public data with no proprietary edge.

## Related skills
`seo-audit` · `schema` · `competitor-pages` · `ai-seo`
