---
type: technique
slug: negative-constraint-prompting
title: Negative-constraint prompting
aliases: [exclusion prompting, no-X constraints, negative space]
models: [seedance-2, seedance-2-fast]
keywords: [negatives, exclusions, authenticity, control, clutter]
confidence: provisional
observations: 1
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---

## What it achieves
Removes unwanted elements the model tends to hallucinate (signage, crowds, commercial clutter, modern polish) by naming them as explicit exclusions, sharpening the intended mood.

## The recipe (copy-paste fragment)
> No stores, advertisements, cafes, crowds, or commercial activity.

Attach exclusions to the block they govern (location gets scene exclusions; camera gets "no stabilization, no cinematic moves, no modern color grading").

## Why it works
Generative video over-populates scenes with generic detail. Explicit negatives prune that back toward the intended authenticity.

## Per-model recipes
- **Seedance 2.0 / SD2 Fast** — inline "No X" phrases within the relevant block work; a scene stays quiet/empty when clutter is excluded.

## Limitations / notes
- Provisional. Too many negatives can flatten a scene — exclude what actively breaks the mood, not everything.
