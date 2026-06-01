---
name: schema
description: When the user wants to add, fix, or optimize schema markup and structured data on a neobank or fintech site. Also use when the user mentions "schema," "structured data," "JSON-LD," "rich results," "FinancialProduct," or "FAQ schema." Covers the schema types that matter for fintech and keeping marked-up financial values accurate and current.
---

# Schema / Structured Data (Neobank / Fintech)

If `product-marketing.md` exists, read it first for entity details and approved claims.

Structured data helps search and AI systems understand your pages and can earn rich results. For fintech, pick the types that match real pages and keep the marked-up values accurate — schema that misstates a fee or rate is the same accuracy problem as the visible page, just machine-readable.

## Types that matter for neobanks
- **Organization / FinancialService** — entity name, logo, sameAs (social/profiles), contact, and any licensing/identifier info. Establishes the entity (supports E-E-A-T and AI entity resolution).
- **FinancialProduct** (and subtypes like `BankAccount`) — for specific account/product pages; mark up fees, rates, and terms **only with current, approved values**.
- **FAQPage** — for genuine Q&A on product, eligibility, and fee pages. Good for fintech because prospects have lots of "is it really free / is it insured / what's the catch" questions.
- **BreadcrumbList** — site structure for comparison/segment hierarchies.
- **Review / AggregateRating** — *use with caution.* Only mark up genuine, verifiable reviews, follow Google's self-serving-review rules, and never fabricate ratings. Misuse risks manual action and, for a financial brand, reputational and regulatory exposure.

## Rules
- **Marked-up values must match the visible page and be current.** Mismatched or stale schema can lose rich results and, for rates/fees/insurance, creates the same inaccuracy risk as visible copy.
- Use **JSON-LD** (Google's preferred format).
- Don't mark up content that isn't actually on the page.
- Validate with the Rich Results Test and Schema validator before shipping.
- For programmatic pages, source rate/fee values into schema from the same single source of truth as the visible copy (see `programmatic-seo`).

## Output
The JSON-LD for each page type, the fields populated, where fact-sensitive values (rates/fees) are sourced from, so they stay consistent with the visible page.
