---
type: use-case
slug: realistic-ugc
title: Realistic UGC / faux-found-footage
aliases: [ugc, found footage, home video, slice-of-life, authentic footage]
models: [seedance-2, seedance-2-fast]
techniques: [camcorder-realism, identity-lock, negative-constraint-prompting, timed-beat-blocking]
keywords: [ugc, authenticity, realism, tiktok, candid, handheld]
confidence: emerging
observations: 2
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---

## Goal
Clips that read as genuine, candid user-generated / home-video footage — the "is this real?" aesthetic — not polished AI.

## Best current stack (as of 2026-07-02)
- **Model:** Seedance 2.0, or SD2 Fast (720p) for speed/cost. 15s, 16:9.
- **Techniques:** [[camcorder-realism]] (the core look) + [[identity-lock]] (stop drift) + [[negative-constraint-prompting]] (kill clutter) + [[timed-beat-blocking]] (pacing).

## Composable prompt template (the 7-block form)
Fill the bracketed fields; keep the camera block and structure close to verbatim.

```
Main subject: [detailed appearance — age, build, specific clothing, hair state, accessories, skin/makeup, demeanor]. Maintain consistent identity, clothing, hairstyle, and appearance throughout the entire video.
Location: [specific real place + time of day + concrete environmental detail]. [Negative exclusions: no stores, ads, crowds, ...].
Visual Style: Ultra-realistic documentary realism. Genuine candid behavior. Natural body language. Unscripted slice-of-life feeling.
Camera Style: Early-2000s consumer DV camcorder aesthetic. Heavy handheld shake, imperfect framing, frequent autofocus hunting, lens breathing, exposure pumping between sun and shade, occasional motion blur, subtle rolling shutter, mild compression artifacts, faded colors, soft contrast, slight sensor noise. No stabilization. No cinematic camera moves. No modern color grading.
00:00-00:02 [beat] . 00:02-00:04 [beat] . 00:04-00:06 [beat] . 00:06-00:08 [beat] . 00:08-00:10 [beat] . 00:10-00:15 [beat, end on a clear stop].
Audio: Natural ambient sound only — [scene-appropriate ambience]. No music. No narration.
Goal: [one-line north star — the feeling to leave the viewer with].
```

## Proven example
The Korean-neighborhood clip ([[20260702-seedance-camcorder-ugc]], 5.36M views) — reproduced in-house on SD2 Fast 720p.

## Limitations / notes
- Confidence emerging (one external + one in-house). Add other-model recipes as references arrive.
