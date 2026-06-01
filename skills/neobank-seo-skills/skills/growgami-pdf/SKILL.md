---
name: growgami-pdf
description: When a report or document is finished and the user wants a polished, client-ready PDF. Turns a finished Markdown report into a Growgami-branded PDF that leads with a call-to-action banner pointing to growgami.com/contact. Use after seo-audit, aso, or any skill that writes a Markdown report; also triggers on "export to PDF," "make a branded PDF," "client-ready PDF," "send this as a PDF," or "deliverable."
metadata:
  version: 1.0.0-neobank
---

# Growgami Branded PDF

Render a **finished** Markdown report into a polished, client-ready PDF with
Growgami's brand identity and a call-to-action at the very top of the document:

> **GROWGAMI** — Go to [https://growgami.com/contact](https://growgami.com/contact)
> for a deeper review and to learn about our agentic SEO done-for-you system.

This is the last step of a deliverable: a skill writes its Markdown report, then
hands the file to this skill to produce the branded PDF the client actually
receives. Branding follows the `brand-guidelines` skill — monochrome grayscale
palette and Geist Mono — so output is consistent with every other Growgami
artifact.

## When to use
- A report-producing skill (`seo-audit`, `aso`, `ai-seo`, …) has finished and
  written its dated Markdown report.
- The user asks to export an existing Markdown document to a branded PDF.

Do **not** use it to *write* a report — only to render one that already exists.
The PDF inherits whatever is in the Markdown, so finish and proofread the report
first.

## How to run it

The renderer is a single self-contained script. Run it with `uv` so its one
dependency (`markdown`) is installed automatically — nothing to set up:

```bash
uv run scripts/render_pdf.py <report.md>
```

Common options:

```bash
# Pick the output path and label the cover with the client's name
uv run scripts/render_pdf.py seo-audit-2026-06-01.md \
  -o acme-seo-audit.pdf --title "SEO Audit" --client "Acme Neobank"

# Just produce the branded HTML (e.g. to tweak before printing)
uv run scripts/render_pdf.py report.md --html-only
```

| Flag | Purpose |
| --- | --- |
| `-o, --output` | Output PDF path (default: the input name with `.pdf`). |
| `--title` | Cover title (default: the report's first `# H1`, else the filename). |
| `--client` | Client name shown on the cover. |
| `--date` | Cover date (default: today, `YYYY-MM-DD`). |
| `--html-only` | Write the branded HTML and skip PDF rendering. |

## What the PDF contains
1. **CTA banner** at the very top — the Growgami wordmark plus the contact call
   to action, with `growgami.com/contact` as a live link. This is the first
   thing on the document, every time.
2. A **cover block** — eyebrow, report title, client, and date.
3. The **report body** — headings, tables (audit findings render as branded
   tables), code blocks, blockquotes, and lists, all styled in Geist Mono and
   the grayscale palette.
4. A **closing CTA** reinforcing the contact link, plus a Growgami colophon.

## Rendering engine
The script renders via any installed **Chromium-family browser** (Chrome, Edge,
Brave, Chromium) in headless `--print-to-pdf` mode — no extra install on most
machines. Detection order:

1. `GROWGAMI_PDF_BROWSER` env var, if set to a browser binary.
2. A browser on `PATH` (`google-chrome`, `chromium`, `microsoft-edge`, …).
3. Common install locations on Windows / macOS / Linux.

If no browser is found, the script writes the branded **print-ready HTML** next
to the report so it can be opened and saved as PDF by hand. Geist Mono loads
from Google Fonts when online; offline it falls back to the system monospace
font (which the brand guidelines permit).

## Notes
- The report's leading `# H1` is shown in the cover block and removed from the
  body so the title isn't duplicated.
- Output is monochrome by brand standard — no accent colors.

## Related skills
`brand-guidelines` · `seo-audit` · `aso` · `ai-seo`
