---
type: technique
slug: timed-beat-blocking
title: Timed-beat blocking
aliases: [timeline prompting, shot beats, timestamped blocking, storyboard prompt]
models: [seedance-2, seedance-2-fast]
keywords: [timeline, beats, pacing, blocking, storyboard, shot list]
confidence: provisional
observations: 1
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---

## What it achieves
Gives a clip deliberate pacing and a mini-narrative by segmenting its duration into timestamped beats, each with a single clear action, instead of one vague run-on description.

## The recipe (copy-paste fragment)
> 00:00-00:02 [action] . 00:02-00:04 [action] . ... one action per 2-3s beat across the full duration, ending on a clear stop.

## Why it works
A single action per short window keeps the model focused and prevents it from cramming or stalling; the sequence reads as intentional direction.

## Per-model recipes
- **Seedance 2.0 / SD2 Fast** — 6 beats over 15s (2-3s each) works well; end on a clear stop ("cuts to black mid-motion") for a natural out.

## Limitations / notes
- Provisional. Match beat count to duration; too many beats in a short clip rushes.
