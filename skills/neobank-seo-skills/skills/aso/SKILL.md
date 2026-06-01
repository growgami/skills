---
name: aso
description: "When the user wants to audit or optimize an App Store or Google Play listing for a neobank or fintech app. Also use for 'ASO audit,' 'app store optimization,' 'optimize my app listing,' 'improve app visibility,' 'app store ranking,' 'why aren't people downloading my app,' 'improve app conversion,' 'app keyword optimization,' or when the user shares an App Store / Google Play URL. For web SEO see seo-audit; for AI answer engines see ai-seo."
metadata:
  version: 2.0.0-neobank
---

<!-- Adapted from coreyhaines31/marketingskills `aso` (MIT). Platform mechanics, scoring framework, and brand-tier model retained (they're store facts, not neobank-specific); neobank additions are the trust/KYC layer, query targets, and review-volatility notes. -->

# ASO Audit — Neobank / Fintech

For a neobank, the app store is a **parallel search engine** — often more installs come from store search than from Google. But it has a fintech-specific trap: the listing's job isn't just to win installs, it's to win *the right* installs, because a finance app loses users at KYC and refunds that loss as 1-star reviews. Optimize for qualified installs, not raw volume.

Read `.agents/product-marketing.md` first; only ask for what's missing.

## Phase 1 — Identify store & fetch
Detect store from URL (`apps.apple.com/.../id{digits}` or `play.google.com/store/apps/details?id=...`). Fetch the listing and extract every field. **Stores render client-side**, so `web_fetch`/`curl` often return incomplete data and *cannot* see screenshot images — take a screenshot of the listing (or ask the user to) to assess icon, screenshots, captions, and video. Note any gaps rather than guessing.

## Phase 1.5 — Brand maturity tier
Score deviations against tier, not absolutes. Most neobanks are **Challenger** (<100K ratings, need keyword discovery — scored strictly) or **Established** (100K+, brand-first titles fine but still include keywords). A handful (Cash App, Chime, Revolut, Nubank) are **Dominant** — brand *is* the keyword, lifestyle screenshots and generic release notes are valid choices. Before docking points, ask: mistake, or data-informed choice by a team with an ASO function?

## Phase 2 — Score each dimension (0–10, weighted /100)

| # | Dimension | Weight | Covers |
|---|---|---|---|
| 1 | Title & Subtitle | 20% | Char usage, keyword presence, brand+keyword balance |
| 2 | Description | 15% | First 3 lines, keyword density (Google), CTA, structure |
| 3 | Visual Assets | 25% | Screenshot count/quality/messaging, video, icon, feature graphic |
| 4 | Ratings & Reviews | 20% | Average, volume, recency, developer responses |
| 5 | Metadata & Freshness | 10% | Category, update recency, localization, data safety |
| 6 | Conversion Signals | 10% | Price/IAP transparency, social proof, downloads |

Grades: 85–100 A, 70–84 B, 50–69 C, 30–49 D, <30 F.

**Neobank weighting note:** Ratings (dim 4) and the trust content of Visual Assets (dim 3) matter more than for a typical app — see below.

## Phase 3 — Competitor comparison (optional)
Fetch 2–3 category competitors, score them the same way, build a gap table, and find keyword gaps (terms they target that the app doesn't).

## Phase 4 — Report
Score card → top 3 quick wins (<1hr, high impact) → per-dimension findings → keyword suggestions → visual recommendations → priority action plan. Every recommendation specific ("change subtitle from X to Y" + char counts), not vague. Note what needs paid tools (search volume, exact rank) and what needs Console access.

---

## Neobank-specific layer

**Keyword targets.** Beyond brand, neobanks compete on category + the same long-tail wedge as web: "early direct deposit," "no fee checking," "send money to [country]," "budgeting," "second chance banking," "[X] for teens/freelancers." Map the title/subtitle/keyword field to differentiators, not generic "banking app."

**Screenshots must sell trust, not just features.** The first 3 (90% never scroll past them) should answer the finance skeptic: security, deposit-insurance/partner-bank framing, no-hidden-fees, real numbers. A finance app that looks unserious loses installs *and* trust.

**Ratings are volatile and load-bearing.** Outages and fund-access complaints tank a banking app's rating fast, and below 4.0 is an always-flag issue. Developer responses to negative reviews matter more here (trust signal). Recommend a review-prompt strategy (Apple: max 3 prompts/365 days) timed after a positive moment (first funded paycheck), not at app open.

**Pre-qualify in the copy to protect ratings.** If eligibility is limited (region, age, KYC requirements), set expectations in the description so rejected users don't leave 1-star "couldn't even sign up" reviews. This is the ASO version of the signup→funded gap.

**Data safety / privacy section (Google Play).** Fill it accurately and completely — incomplete or mismatched data-safety info is a store-policy and trust problem. (Accuracy/store-policy only; legal adequacy is the client's call, not this skill's.)

**Localization to licensed markets only** — score relative to actual served markets, not absolute language count.

---

## Platform facts (kept inline; for exhaustive specs use official Apple App Store / Google Play docs)

**Apple:** Title (30) + Subtitle (30) + hidden Keyword field (100 *bytes*, comma-separated no spaces, never repeat words across fields) = indexed. Long description NOT indexed (conversion only). Screenshots up to 10, first 3 in search, captions indexed since 2025. Preview video (up to 3, 15–30s, autoplays muted, +20–40% conversion). Custom Product Pages in organic search. Editorial curation rewards quality/design.

**Google Play:** Title (30) + Short desc (80) + Full desc (4,000, IS indexed, ~2–3% density, no stuffing) = indexed. No hidden keyword field. Title prohibits emojis/ALL CAPS/"best"/"#1"/"free"/CTAs. Screenshots min 2 max 8. Feature graphic (1024×500) needed for featuring. Video rarely played (low ROI). **Android Vitals affect ranking** — crash >1.09% or ANR >0.47% reduces visibility (relevant: a banking app crashing erodes both rank and trust).

## Always-flag checklist
Rating <4.0; last update >3 months; Google Play no keyword strategy or missing feature graphic; likely repeated words across Apple fields; category mismatch; <5 screenshots; first 3 screenshots don't address trust; eligibility not set in copy.

## Related skills
`seo-audit` · `ai-seo` · `competitor-pages`
