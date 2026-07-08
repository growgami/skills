---
type: technique
slug: identity-lock
title: Subject identity lock
aliases: [consistency clause, character consistency, appearance lock]
models: [seedance-2, seedance-2-fast]
keywords: [consistency, identity, drift, character, wardrobe, continuity]
confidence: provisional
observations: 1
sources: [20260702-seedance-camcorder-ugc]
updated: 2026-07-02
---

## What it achieves
Keeps a subject's face, clothing, hair, and overall appearance consistent across an entire clip, preventing the frame-to-frame drift that betrays AI video — especially under camera motion.

## The recipe (copy-paste fragment)
> Maintain consistent identity, clothing, hairstyle, and appearance throughout the entire video.

Place it at the END of the subject description, after a detailed appearance spec.

## Why it works
A concrete appearance spec plus an explicit persistence instruction gives the model a fixed target to hold across frames. Most effective when appearance is described concretely (specific garments, hair state) rather than vaguely.

## Per-model recipes
- **Seedance 2.0 / SD2 Fast** — the explicit clause noticeably reduces drift; pair with concrete wardrobe detail. Especially needed alongside [[camcorder-realism]], because simulated handheld motion increases drift risk.

## Limitations / notes
- Provisional (single reference). Does not fully eliminate drift on long or complex motion.
