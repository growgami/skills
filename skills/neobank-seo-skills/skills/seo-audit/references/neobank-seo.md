# Neobank SEO — Reference

Deep material for the `seo-audit` skill. Loaded on demand so `SKILL.md` stays scannable.

## Why neobank SEO is structurally different

- **Un-indexable product.** The app lives behind login. The indexable surface is a thin marketing site, so SEO leverage is unusually concentrated and the "thin content" finding needs context (it's structural, not laziness).
- **Paid channels are gated.** Google/Meta restrict financial-services ads; crypto ads are largely banned. Organic + ASO are among the few un-gated scalable channels, so they're strategically over-weighted vs. a normal SaaS.
- **YMYL.** "Your Money or Your Life" pages face a higher E-E-A-T bar in Google's Quality Rater Guidelines. Trust signals and accuracy are ranking factors, not polish.
- **Adversarial SERP.** Affiliate publishers own head money terms with authority you can't match head-on. Triage by winnability.

## The surface map

A neobank's discovery footprint, in rough order of SEO leverage:

1. **Marketing site (.com)** — primary surface; usually a JS-rendered SPA. Crawlability/indexability of this is the most common real problem.
2. **Branded SERP** — not a page you own but a surface you must control: login, routing number, fees, reviews, "is it safe/legit," "app down."
3. **Help center / docs** — often a subdomain or third-party (Zendesk/Intercom). Ranks for support + "how do I"; check it isn't orphaned from main-site authority.
4. **App Store / Play Store** — ASO is a parallel search engine; for many neobanks store search drives more installs than web. Hand to `aso`.
5. **Blog / learn center** — E-E-A-T and long-tail capture, if it exists.
6. **Off-site reputation** — review/comparison sites, Reddit, Trustpilot, CFPB complaint database, and AI answer engines. Monitored, not controlled.
7. **Localized/jurisdiction variants** — only where licensed.

## Query taxonomy + winnability

| Class | Examples | Intent | Winnable? |
| --- | --- | --- | --- |
| Branded | `[brand] login`, `[brand] routing number`, `is [brand] safe` | Very high | Yes — and must defend |
| Comparison (head) | `best bank account`, `best neobank` | High | Usually **no** head-on (affiliate moat) |
| Comparison (your name) | `[brand] vs X`, `X alternatives` | High | Often yes — own your own comparisons |
| Feature / use-case | `early direct deposit`, `account no SSN`, `second chance banking`, `send money to [country]` | High | **Yes — the wedge** |
| Support / how-to | `how to set up direct deposit`, `change PIN` | Mixed | Yes via help center; builds E-E-A-T |
| Educational (TOFU) | `what is a neobank`, `is mobile banking safe` | Low | Yes for E-E-A-T + AI citation; low direct ROI |

**Winnability rubric** — score a target query before recommending effort:
- SERP composition: are the top results entrenched publishers, or beatable? (If 8/10 are NerdWallet-class, deprioritize.)
- Intent match: can your *product* actually satisfy it better than a listicle?
- Differentiator fit: does it map to something you do that incumbents don't?
- Surface fit: is this better served on the marketing site, help center, or app store?
- Effort vs. expected funded-account value.

## Trust / E-E-A-T checklist (YMYL)

On money pages:
- Visible legal entity name and licensing/regulatory info.
- Partner-bank / deposit-insurance disclosure in the **approved phrasing** (never paraphrased into something new).
- Current rates/fees with visible last-updated dates.
- Security details; clear contact info; privacy policy and terms.

Site-wide:
- Robust About / Legal / Security pages (treated as ranking-relevant).
- Named authors with credentials and sourced claims on educational content.
- Healthy off-site reputation (store ratings, reputable roundups, controlled "is it safe" SERP).

## Freshness & consistency (SEO hygiene, not legal review)

- **Single source of truth** for rate/fee/feature values, feeding both visible copy and JSON-LD, so an update propagates everywhere at once.
- **Schema parity:** marked-up values must match the visible page; stale schema loses rich results and gets quoted wrong by AI.
- **Templated pages multiply staleness:** one outdated value becomes hundreds of outdated URLs — drive them all from the same source.
- **AI surface:** answer engines may quote old numbers; keep facts current and single-sourced, and check periodically.
- This is purely about inconsistent/outdated information hurting rankings and AI citation. Whether any claim is legally adequate is the client's responsibility, not the skill's.

## Measurement

Instrument the full chain, not sessions:
`organic visit → signup → KYC completion → funded account → 30/90-day retention`

- North-star: **funded, KYC-passed accounts** (and direct-deposit set), by query/page cluster.
- Watch the **signup → funded gap**: a large gap means traffic that doesn't convert to a real customer (wrong intent, or KYC friction).
- Re-audit on a schedule and diff: regressions in indexation, branded-SERP control, and stale/conflicting facts are the ones that hurt most.
