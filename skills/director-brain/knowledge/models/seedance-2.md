---
type: model
slug: seedance-2
title: Seedance 2.0 (ByteDance)
aliases: [SD2, SD2 Fast, seedance-2-fast, seedance 2.0]
techniques: [camcorder-realism, identity-lock, negative-constraint-prompting, timed-beat-blocking]
use_cases: [realistic-ugc]
keywords: [text-to-video, image-to-video, bytedance, openart, higgsfield, realism]
confidence: emerging
observations: 2
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---

## What it is
ByteDance's Seedance 2.0 text/image-to-video model. A **Fast** tier ("SD2 Fast") trades some fidelity for speed/cost and reproduces the same looks at lower resolution (720p verified).

## Access / providers
- **OpenArt AI** — text-to-video, observed at 16:9 1080p, ~15s.
- **Higgsfield** (`platform.higgsfield.ai`) — exposes `seedance` as **image-to-video only** (needs an input image); for pure text-to-video use `minimax-t2v`. API auth works via injected creds but was blocked on an empty credit pool as of 2026-07-02.
- Also carried on fal.ai / Replicate (text-to-video) — unverified from our environment.

## Strengths (observed)
- Exceptional photoreal "authentic footage" look when prompted for imperfection — see [[camcorder-realism]].
- Holds a subject well with an explicit [[identity-lock]] clause.
- Responds to structured, multi-block prompts (subject / location / style / camera / beats / audio / goal) and to [[timed-beat-blocking]].

## Prompt dialect
Rewards long, rigidly-structured prompts. The 7-block template (see [[realistic-ugc]]) is the proven form. Inline negatives per block work ([[negative-constraint-prompting]]).

## Params
- Resolution 1080p (OpenArt) / 720p (SD2 Fast). Aspect 16:9 verified. Duration ~15s verified.

## Limitations / notes
- Higgsfield's Seedance is image-to-video only — a gotcha if you expect text-to-video there.
- Fast tier lowers resolution; the aesthetic survives the drop.
- Confidence emerging (one external reference + one in-house reproduction).
