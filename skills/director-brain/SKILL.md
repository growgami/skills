---
name: director-brain
description: A living AI-video directing playbook. Use this skill (a) to DIGEST a shared reference (tweet, video, prompt, screenshot, link) into reusable directing knowledge, or (b) to ANSWER a directing question like "best SD2 Fast prompt for realistic UGC" or "how do I get this camera move in Veo". It merges every reference into cross-indexed technique/model/use-case knowledge (never duplicating) and composes answers from everything learned so far, growing each time it is used.
---

# Director Brain

A continuously-enriched directing playbook for AI video/image generation. It turns every reference someone shares into **reusable directing knowledge** — not a prompt library, a playbook that learns how to get the best out of each model.

Two jobs: **INGEST** a new reference into the knowledge base (merging, never duplicating), and **QUERY** the knowledge base to compose an answer.

## Knowledge model

The atomic unit is a **technique** — a named, reusable directing move (a camera behavior, lighting setup, realism trick, motion pattern, composition rule). Techniques carry per-model recipes. Models and use-cases are indexes that aggregate over techniques.

Layout (all under `knowledge/`):

- `techniques/<slug>.md` — one reusable directing move. The core asset.
- `models/<slug>.md` — per-model profile: what it is good/bad at, param ranges, prompt dialect, techniques it nails vs struggles with.
- `use-cases/<slug>.md` — playbook for an outcome (e.g. realistic-ugc): the winning model + technique stack + a composable prompt template.
- `references/<YYYYMMDD>-<slug>.md` — a digest record per ingested reference: source, what it demonstrated, which entries it created/enriched. Provenance + dedup audit trail.
- `INDEX.md` — the discovery layer: a tag/keyword map pointing to entries. Regenerated as entries change.

Every knowledge file starts with YAML frontmatter for retrieval:

```
---
type: technique | model | use-case | reference
slug: <kebab>
title: <human title>
aliases: [SD2 Fast, seedance-fast]        # alternate names people use
models: [seedance-2, seedance-2-fast]     # which models covered/referenced
techniques: [camcorder-realism]           # which techniques referenced
use_cases: [realistic-ugc]
keywords: [handheld, found-footage, ugc, korean, slice-of-life]
confidence: provisional | emerging | validated
observations: 1                            # how many references support this
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---
```

**Confidence ladder:** `provisional` (1 reference) -> `emerging` (2-3, consistent) -> `validated` (4+ across sources/creators, or reproduced by us). Bump on each corroborating ingest; downgrade/annotate on conflict.

## INGEST workflow

When a reference is shared (a tweet/video/prompt/screenshot, or a link):

1. **Extract.** Pull the raw facts: model + version + provider, params (resolution, duration, aspect, seed, steps, speed tier), the prompt (verbatim if given), and the directing content — cinematography, camera/motion, lighting, composition, subject/identity handling, audio, pacing/beats, plus quality notes and limitations. Note the source (URL, author, date, engagement if notable) and whether we reproduced it.
2. **Classify.** Decide which technique(s) it demonstrates, which model(s), which use-case(s). Prefer reusing existing slugs — grep `knowledge/` and read `INDEX.md` first.
3. **Merge, don't duplicate.** For each technique/model/use-case:
   - **Match found** -> open that file, fold in the new data point (add the per-model recipe, refine the description, add the prompt fragment as a variant), append the source, bump `observations` and `confidence`, update `updated`. If the new data *conflicts* with existing, keep both and annotate the condition ("at 720p SD2 Fast, X; at 1080p, Y").
   - **No match** -> create a new file from the template.
4. **Log the reference.** Always write `references/<date>-<slug>.md`: source, one-paragraph what-it-demonstrated, a bullet list of which knowledge entries it created/enriched (with links), and the raw prompt (provenance only). This is the dedup trail — a similar prior reference here means merge instead of create.
5. **Update INDEX.md** with any new slugs/keywords.
6. Keep prompt fragments **copy-paste ready** and generic (placeholders for subject/setting), so they compose.

## QUERY workflow

When someone asks a directing question ("best SD2 Fast prompt for realistic UGC", "how do I get this camera move in Veo", "what do we know about Kling limits"):

1. **Classify the axis:** model? technique? use-case? outcome? Often several.
2. **Retrieve.** Grep frontmatter tags (`models:`, `techniques:`, `use_cases:`, `keywords:`, `aliases:`) and INDEX.md for matches. Pull the highest-confidence relevant entries.
3. **Compose, don't dump.** Synthesize an answer: recommend the technique(s) + model recipe, give the composable prompt fragment/template, cite the confidence level and the source references, and flag known limitations. If confidence is provisional, say so.
4. If nothing matches, say what is missing — that is a gap to fill on the next ingest.

## Conventions

- Slugs kebab-case; dates YYYYMMDD.
- One technique = one move. If a reference bundles several (the "camcorder realism" recipe is really identity-lock + handheld/autofocus camera + negative-constraint prompting + timed-beat structure), split into separate technique files and let the use-case/reference tie them together.
- Never store a raw prompt as the knowledge — extract the *pattern*; keep the raw prompt only inside the reference log for provenance.
- Prefer evolving a file over adding one. Duplicates are the failure mode.
