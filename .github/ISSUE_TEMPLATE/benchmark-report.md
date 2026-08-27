---
name: Benchmark report
about: Record a reproducible Brainwaves serving or LongWriter result
title: "[benchmark] "
labels: benchmark
assignees: ''
---

## Identity

- Profile / runtime:
- Git commit:
- Model revision:
- Report or release artifact:

## Hardware and configuration

- GPU / VRAM / gfx:
- ROCm / HIP / PyTorch / Transformers:
- vLLM or SGLang version/commit:
- BF16 weights, KV dtype, YaRN parameters:
- AITER, MTP, prefix caching, chunked prefill, offload:

## Workload

- Input / output tokens:
- Scenario and fixture revision:
- Seed / sampling profile:
- Concurrency:

## Measurements

| Metric | Value |
|---|---|
| TTFT | |
| Prefill tok/s | |
| Decode tok/s | |
| ITL | |
| Peak HBM / CPU RAM | |
| Prefix query / hit / reused tokens | |
| GDN state slots | |
| Failures / OOM / disconnects | |

## Quality and decision

- Retrieval / continuity score:
- Voice / dialogue / fluency / coherence / pacing scores:
- Repetition and knowledge leakage:
- Label (`EXCELLENT`, `PRODUCTION`, `USABLE`, `DEGRADED`, `EXPERIMENTAL`, `FAILED`):

Paste safe reproduction commands. Never include keys, private prompts, raw
unrestricted manuscripts, or unblinded A/B mappings.
