# Director Brain — Index

Discovery layer. Grep here first, then open the entry. Regenerate when entries change.

## Models
- [seedance-2](models/seedance-2.md) — Seedance 2.0 / SD2 Fast. text/image-to-video. aliases: SD2, SD2 Fast.

## Techniques
- [camcorder-realism](techniques/camcorder-realism.md) — early-2000s DV camcorder look. keywords: found-footage, handheld, faded colors, sensor noise.
- [identity-lock](techniques/identity-lock.md) — keep subject consistent across a clip. keywords: consistency, drift.
- [negative-constraint-prompting](techniques/negative-constraint-prompting.md) — "no X" exclusions. keywords: negatives, clutter.
- [timed-beat-blocking](techniques/timed-beat-blocking.md) — timestamped shot beats. keywords: timeline, pacing.

## Use cases
- [realistic-ugc](use-cases/realistic-ugc.md) — faux-found-footage UGC. Stack: seedance-2 + camcorder-realism + identity-lock + negatives + beats.

## References (ingest log)
- [20260702-seedance-camcorder-ugc](references/20260702-seedance-camcorder-ugc.md) — @john_my07 Korean-neighborhood clip; reproduced on SD2 Fast 720p.

## Query cheatsheet
- "best <model> prompt for <use-case>" -> open the use-case playbook, then the model profile for param/dialect specifics.
- "how do I get <look/motion> in <model>" -> open the technique, read its per-model recipe.
- "what do we know about <model>" -> the model profile.
