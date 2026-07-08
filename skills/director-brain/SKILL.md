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

1. **Watch the video with Gemini.** This is the primary extraction step. When the reference includes a clip, have Gemini *watch the actual footage* and read the directing content straight from the frames and audio — camera work, motion, lighting, composition, and pacing — instead of inferring it secondhand from the shared text/prompt. Prompt Gemini to return the breakdown as the structured fields this skill already uses (**camera / motion / lighting / composition / pacing**) so it drops straight into the next step. See *Watching the video with Gemini* below for the copy-pasteable call. Then capture the surrounding raw facts from the shared post: model + version + provider, params (resolution, duration, aspect, seed, steps, speed tier), the prompt (verbatim if given), plus quality notes and limitations. Note the source (URL, author, date, engagement if notable) and whether we reproduced it. (If no video is attached — only a prompt/screenshot — skip the watch and extract the directing content from the text as before.)
2. **Classify.** Decide which technique(s) it demonstrates, which model(s), which use-case(s). Prefer reusing existing slugs — grep `knowledge/` and read `INDEX.md` first.
3. **Merge, don't duplicate.** For each technique/model/use-case:
   - **Match found** -> open that file, fold in the new data point (add the per-model recipe, refine the description, add the prompt fragment as a variant), append the source, bump `observations` and `confidence`, update `updated`. If the new data *conflicts* with existing, keep both and annotate the condition ("at 720p SD2 Fast, X; at 1080p, Y").
   - **No match** -> create a new file from the template.
4. **Log the reference.** Always write `references/<date>-<slug>.md`: source, one-paragraph what-it-demonstrated, a bullet list of which knowledge entries it created/enriched (with links), and the raw prompt (provenance only). This is the dedup trail — a similar prior reference here means merge instead of create.
5. **Update INDEX.md** with any new slugs/keywords.
6. Keep prompt fragments **copy-paste ready** and generic (placeholders for subject/setting), so they compose.

### Watching the video with Gemini

Gemini watches the real clip and returns the directing breakdown. In the Claude Tag environment the agent proxy transparently injects the `x-goog-api-key` header, so **no API key goes in the request** — plain `curl` works.

- **Host:** `generativelanguage.googleapis.com` (credential is proxy-injected; do not add a key).
- **Model:** `gemini-2.5-flash` (default). Use `gemini-2.5-pro` for harder analyses.
- **Gotcha:** `gemini-2.0-flash` and the entire `gemini-1.5` family are **retired** and return `404` — do not use them.
- **Endpoint:** `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- Ask Gemini to return the breakdown as the fields the knowledge base uses (**camera / motion / lighting / composition / pacing**) so it feeds straight into Classify → Merge.

**Path A — public YouTube URL (validated).** Simplest; no upload. Pass the URL as a `fileData.fileUri` part alongside the extraction prompt:

```bash
curl -sS \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[
    {"text":"Watch this video. Extract the directing as structured fields — camera (lens, framing, angles, cuts), motion (subject + camera movement), lighting (sources, quality, color), composition, pacing (beats, cut rhythm). Be concrete and reusable."},
    {"fileData":{"fileUri":"https://www.youtube.com/watch?v=VIDEO_ID"}}
  ]}]}'
```

Validated end-to-end on 2026-07-08 (HTTP 200; ~167K video + ~20K audio prompt tokens billed, confirming real frame + audio ingestion).

**Path B — non-YouTube clip / upload / S3 / local file (documented, untested in this env).** Use the resumable File API, then reference the uploaded file in `generateContent`:

1. **Start** the upload (capture the upload URL from the `x-goog-upload-url` response header):

   ```bash
   curl -sS -D - -o /dev/null \
     "https://generativelanguage.googleapis.com/upload/v1beta/files" \
     -H "X-Goog-Upload-Protocol: resumable" \
     -H "X-Goog-Upload-Command: start" \
     -H "X-Goog-Upload-Header-Content-Length: $(stat -c%s clip.mp4)" \
     -H "X-Goog-Upload-Header-Content-Type: video/mp4" \
     -H "Content-Type: application/json" \
     -d '{"file":{"display_name":"clip"}}'
   ```

2. **Upload + finalize** the bytes to that URL:

   ```bash
   curl -sS "$UPLOAD_URL" \
     -H "Content-Length: $(stat -c%s clip.mp4)" \
     -H "X-Goog-Upload-Offset: 0" \
     -H "X-Goog-Upload-Command: upload, finalize" \
     --data-binary @clip.mp4
   ```

   The response returns the file resource (`file.name`, `file.uri`, `file.mimeType`).

3. **Poll** `GET https://generativelanguage.googleapis.com/v1beta/{file.name}` until `state == ACTIVE`.

4. **Reference** it in `generateContent` with a `fileData` part carrying `mimeType` + `fileUri`:

   ```json
   {"contents":[{"parts":[
     {"text":"<same extraction prompt as Path A>"},
     {"fileData":{"mimeType":"video/mp4","fileUri":"<file.uri>"}}
   ]}]}
   ```

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
