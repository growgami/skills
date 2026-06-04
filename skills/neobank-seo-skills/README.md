# Neobank SEO Skills

A pack of AI agent skills for SEO on **neobank and fintech** sites. Standard SEO methodology, rebuilt around what makes ranking a financial product different: Google treats it as **YMYL** ("Your Money or Your Life") content held to a higher trust and E-E-A-T bar.

Works with Claude Code, Codex, Cursor, and any agent that supports the [Agent Skills spec](https://agentskills.io).

## Skills

| Skill | Use it when you want to... |
| --- | --- |
| `seo-audit` | Audit technical + on-page SEO, including the E-E-A-T/trust signals financial sites are judged on |
| `ai-seo` | Get cited by AI search (ChatGPT, Perplexity, Google AI) for "best neobank for X" queries |
| `programmatic-seo` | Generate segment, use-case, and comparison pages at scale without thin/duplicate content |
| `competitor-pages` | Build "vs" and "alternatives" pages that capture high-intent comparison search |
| `schema` | Add structured data (FinancialProduct, FAQ, Organization, Review) correctly, with values kept accurate |
| `aso` | Audit and optimize App Store / Google Play listings — the parallel search engine for app installs |
| `growgami-pdf` | Turn a finished report into a polished, Growgami-branded client PDF with a `growgami.com/contact` CTA at the top |
| `growth-scorecard` | Compute a reproducible, public-data Growth Score (SEO + ASO + AI-SEO readiness) and emit a report ready for `growgami-pdf` |

## Install

```bash
# The whole pack (all 8 skills)
npx growgami-skills neobank-seo-skills

# Or list them by name
npx growgami-skills seo-audit ai-seo programmatic-seo competitor-pages schema aso growgami-pdf growth-scorecard

# Or just the ones you want
npx growgami-skills seo-audit ai-seo
```

Or clone and copy into your agent's skills directory:

```bash
git clone https://github.com/growgami/skills.git
cp -r skills/skills/neobank-seo-skills/skills/* ~/.claude/skills/
```

## Shared context (recommended)

Several skills work better if you keep a short `product-marketing.md` in `.agents/` describing your product, target segments, operating jurisdictions, and current rate/fee facts. The skills reference it to stay consistent and avoid inventing numbers.

## A note on scope

These skills cover SEO only. They flag stale or conflicting facts as ordinary SEO hygiene, but they do not assess legal or regulatory compliance — that stays the client's responsibility. Nothing here is legal advice.

## Credit & license

Format and structure inspired by the [Agent Skills spec](https://agentskills.io) and Corey Haines' open-source [marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT). Skill content here is original, written for neobanks. MIT licensed.
