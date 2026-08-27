# Evaluation methodology

Every profile is run on the same nested fixtures, seed list, and sampling
profile. A profile is not promoted because it accepts `max_model_len`.

## Required dimensions

* Retrieval: single needles at 5/10/25/50/75/90/95%, multi-needle synthesis,
  distractors, and lost-middle.
* Story state: knowledge boundaries, temporal causality, possessions, injuries,
  emotional residue, promises, relationship dimensions, and character agency.
* Writing: voice, dialogue, fluency, rhythm, subtext, comic timing, romantic
  tension, pacing, POV/tense, callback naturalness, and slow-burn control.
* Endurance: 2.5K/5K/10K/20K-token generations and a persistent multi-chapter
  loop where state is not wiped between chapters.
* Systems: TTFT, prefill/decode throughput, ITL, HBM, recurrent-state pool,
  prefix hits, chunked prefill interference, concurrency, failures, and OOMs.

## Gates

`EXCELLENT` means no meaningful quality loss from native. `PRODUCTION` allows a
minor measured trade-off. `USABLE` has noticeable but acceptable degradation.
`DEGRADED`, `EXPERIMENTAL`, and `FAILED` are never default Story OS profiles.
The continuity gate is ≥90% machine checks with no knowledge-boundary failure;
the writing gate is a blinded mean ≥4/5 with voice, dialogue, fluency, and
coherence each ≥3/5. These are initial gates and are recorded with each report.

## Fairness and blinding

Native, 512K, and 1M use nested corpora and identical seeds. Candidate names are
removed from subjective output dossiers; A/B order is randomized. Multiple judge
providers can consume the common schema. Machine metrics are evidence, not a
replacement for human review.
