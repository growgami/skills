---
name: seo-audit
description: When the user wants to audit, review, or diagnose SEO for a neobank, fintech, or digital banking product. Also use for "SEO audit," "technical SEO," "why am I not ranking," "traffic dropped," "lost rankings," "not in Google," "core web vitals," "crawl/indexing issues," "branded search," "is my site safe in search," "E-E-A-T," or "YMYL." Start here even for vague asks like "help with SEO." For pages at scale see programmatic-seo; for structured data see schema; for AI answer engines see ai-seo; for app store search see aso.
metadata:
  version: 3.0.0-neobank
---

<!-- Adapted from coreyhaines31/marketingskills `seo-audit` (MIT). Technical checklist, schema-detection limitation, CWV thresholds, and evidence-based output format retained from the original; the procedure, surface model, winnability triage, and branded-SERP defense are neobank-specific additions. -->

# SEO Audit — Neobank / Fintech

You are auditing organic search for a **regulated, login-gated financial product**. Three facts make this different from a normal SEO audit, and they drive the whole procedure:

1. **The product is mostly un-indexable.** The value lives behind login. The only thing Google sees is a usually-thin, often JS-rendered marketing site. So crawlability of that shell and the existence of *any* indexable surface worth ranking come first — not title tags.
2. **It's YMYL and adversarial.** Google holds financial pages to a higher E-E-A-T/trust bar, and entrenched affiliate publishers (NerdWallet, Bankrate, etc.) own the head money terms. You cannot out-authority them head-on, so **triage by winnability** instead of auditing everything equally.
3. **Freshness matters.** Rates, fees, and features change often. Pages or schema that show stale or self-contradictory numbers hurt rankings and get quoted wrong by AI engines. Flag inconsistency and staleness as ordinary SEO hygiene — do not opine on whether any claim is legally compliant; that is the client's job.

Read `references/neobank-seo.md` for the surface map, query taxonomy, winnability rubric, and trust checklist. Keep this file as the procedure.

---

## How to run this audit

It's a staged procedure. Run all stages for a full audit, or a single stage on request. Be honest about what your tools can and can't verify (see the tool-limits box) and route to the right tool rather than guessing. Emit the result to a dated report file so the audit can be re-run and diffed over time.

### Stage 0 — Intake
Read `.agents/product-marketing.md` (or `.claude/product-marketing.md`) first; only ask for what's missing:
- Domain(s), and **all surfaces**: marketing site, help center, blog, status page, app store listings.
- **Operating jurisdictions** (and which regions are geoblocked).
- Top 3–5 organic competitors (include the affiliate publishers that rank for your money terms).
- Current rates/fees/feature facts (so the audit can spot stale or conflicting numbers across pages — an SEO/freshness check, not a legal one).
- Access to Search Console / analytics / a JS-rendering crawl (Screaming Frog export).
- Primary business metric (almost always *funded, KYC-passed accounts* — not signups or sessions).

### Stage 1 — Map the surfaces
Enumerate the real discovery footprint before auditing any of it (see reference file for the full map). At minimum: marketing .com, help/docs (often a subdomain or Zendesk/Intercom — check it inherits authority and isn't orphaned), blog, App Store + Play Store listings (ASO — a parallel search engine; hand off to the `aso` skill), and off-site reputation (review sites, Reddit, Trustpilot, CFPB complaints, AI answers). An audit scoped to "the website" misses most of the surface.

### Stage 2 — Crawlability & indexation (do this first)
For a neobank this is usually where the real problems are.
- **JS rendering:** is the marketing site server-rendered / pre-rendered, or a client-side SPA? Fetch a key page and check whether primary content and links exist in the raw HTML. If content only appears after JS execution, confirm Google renders it (URL Inspection → rendered HTML) — don't assume.
- robots.txt: unintentional blocks, sitemap reference. XML sitemap: exists, only canonical/indexable URLs, submitted.
- Index status: `site:` check + Search Console coverage; indexed vs. expected. Watch for index bloat from thin/templated pages.
- Canonicalization: self-referencing canonicals on unique pages; HTTPS, www, trailing-slash consistency; no redirect chains/loops or soft 404s.
- Orphan pages; important pages within ~3 clicks.

> **Schema/JS detection limit:** `web_fetch` and `curl` strip `<script>` tags and can't see JS-injected JSON-LD or client-rendered content. To check schema or SPA rendering, use a **browser tool** (`document.querySelectorAll('script[type="application/ld+json"]')`), the **Rich Results Test** (renders JS), or a **Screaming Frog** export. Reporting "no schema / no content" from `web_fetch` alone produces false findings.

### Stage 3 — Trust & E-E-A-T (the primary ranking factor here)
In YMYL this outweighs most on-page tweaks. Check:
- Visible legal entity, licensing/regulatory info, and **partner-bank / insurance disclosure using the approved phrasing** on money pages.
- Robust About / Legal / Security pages — these are ranking-relevant trust signals, not boilerplate.
- Named authors with relevant credentials and sourced claims on educational content (anonymous YMYL content underperforms).
- Off-site reputation: App Store/Trustpilot ratings, presence in reputable roundups, and what "is [brand] safe/legit" SERPs currently show.

### Stage 4 — Branded SERP & reputation defense (high value, usually ignored)
Branded queries are huge volume and high intent. For each of: `[brand]`, `[brand] login`, `[brand] routing number`, `[brand] fees`, `[brand] reviews`, `is [brand] safe/legit`, `[brand] app down` — check who ranks. Flag: phishing/lookalike domains on `login`, aggregators or negative content outranking you on `safe/legit/reviews`, missing or unowned answers. Owning the branded SERP often beats chasing new head terms.

### Stage 5 — Money-page intent & winnability triage
Map target queries to the taxonomy and score winnability (rubric in reference file). Be blunt:
- **Head comparison terms** ("best bank account") — usually *not winnable* head-on vs. affiliate publishers. Note it; don't recommend pouring effort there.
- **Long-tail feature/use-case** ("early direct deposit," "account with no SSN," "second chance banking," "send money to [country]") — the winnable wedge; map each to a product differentiator.
- **Support / "how do I"** — capture via help center; builds E-E-A-T.
Then audit the pages that target winnable intent for depth, intent match, internal links, and cannibalization. (For building these at scale, hand to `programmatic-seo`; for vs/alternatives pages, `competitor-pages`.)

### Stage 6 — Technical foundations
Condensed from standard SEO; verify don't belabor:
- Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1 (mobile first — most traffic and conversion is mobile).
- HTTPS everywhere, valid cert, no mixed content, HTTP→HTTPS redirects (also a visible trust signal here).
- Mobile parity on money pages; readable, consistent URLs.
- International: only index locale/region pages for jurisdictions you're **licensed** in; correct hreflang (self-referencing + reciprocal, valid codes, x-default); never cross-locale canonical.

### Stage 7 — Freshness & consistency check
Crawl indexed pages and JSON-LD for rate/fee/feature numbers and check they're consistent with each other and not stale (e.g., one page says 4.5% APY, another says 4.0%). Conflicting or outdated facts hurt rankings and get quoted wrong by AI engines. Recommend a **single source of truth** feeding both visible copy and schema, plus visible last-updated dates. This is SEO hygiene only — flag inconsistency/staleness, never judge legal compliance.

### Stage 8 — Sibling surfaces
Note (and hand off): **ASO** (`aso` skill) for App/Play Store search, and **AI search** (`ai-seo` skill) for being cited correctly by answer engines — a wrong, stale fee quoted by an AI is worse than not being cited.

---

## Output

Write a dated report (e.g., `seo-audit-YYYY-MM-DD.md`). Structure:

**Executive summary** — overall health, top 3–5 priorities, quick wins, and the one structural issue (often: indexability of the SPA, or a lost branded SERP).

**Findings**, grouped by stage. For each:
- **Issue** — what's wrong
- **Impact** — High / Med / Low (weight branded-SERP, indexability, and trust/E-E-A-T issues up)
- **Evidence** — how you found it, with the tool used
- **Fix** — specific recommendation
- **Winnability** — for query/content findings: is the effort worth it vs. the competition?

**Prioritized action plan** — (1) blockers (indexation, conflicting/stale facts), (2) branded-SERP & trust, (3) winnable long-tail, (4) long-term.

**Diff vs. last run** — if a prior report exists, list what regressed or resolved.

---

## Tool honesty
State what you verified vs. inferred. If you lack a JS-rendering crawler, Search Console access, or browser, say so and tell the operator which check needs which tool rather than reporting a guess as a finding.

## References
- `references/neobank-seo.md` — surface map, query taxonomy, winnability rubric, trust checklist, measurement.

## Related skills
`aso` · `ai-seo` · `programmatic-seo` · `competitor-pages` · `schema`
