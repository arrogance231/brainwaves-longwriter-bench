# Brainwaves MI300X LongWriter Bench

`brainwaves-longwriter-bench` is a reproducible serving and evaluation project
for [`nightmedia/Qwen3.8-27B-Brainwaves`](https://huggingface.co/nightmedia/Qwen3.8-27B-Brainwaves)
on an AMD Instinct MI300X. It tests whether a 27.8B BF16 hybrid Gated DeltaNet
model can sustain plot state, character knowledge, emotional residue, prose
quality, and generation stability at **262K native**, **512K YaRN×2**, and
approximately **1.01M YaRN×4** context.

This is not a claim that 1M is native. The checkpoint config declares 262,144
native positions; longer profiles are reversible runtime YaRN overrides. A
context length is promoted only after the story benchmark passes retrieval,
continuity, writing-quality, and stability gates.

## Current status

The exact model revision currently pinned is
`f9545772aab3abcb84b2f1822134a1c4a052669f`. It is downloaded locally at
`/models/Qwen3.8-27B-Brainwaves` and verified as BF16 with 27,781,427,952
parameters. The MI300X host has 205.8 GB VRAM (gfx942), and the tested serving
image is `vllm-rocm:0.28.0-gfx942` (vLLM 0.28.0, PyTorch 2.12 ROCm 7.2.3,
Transformers 5.16.1).

The first measured result is deliberately conservative: native 262K loads and
completes a 232K-token fiction fixture, but with 259–290 s TTFT. The 512K
YaRN×2 and 1.01M YaRN×4 servers load but produced no first token in bounded
single-request pilots (~9 minutes and ~5 minutes respectively). They are not
advertised as usable context. See [`reports/FINAL_REPORT.md`](reports/FINAL_REPORT.md)
for throughput, cache, FP8, AITER, MTP, and quality evidence.

## What is being tested?

Retrieval asks whether a fact can be found. Long-form fiction additionally asks
whether the model remembers why that fact matters: who learned it, which promise
it changed, how an argument left emotional residue, and whether a later callback
feels natural rather than like an index lookup. `Arro LongWriter Bench` uses a
nested, deterministic, newly written school romantic-comedy AU to test those
properties without redistributing source passages.

## Verified architecture

The actual config is `Qwen3_5ForConditionalGeneration` with a vision tower and
text-only serving mode available. Its text stack has 64 layers (48
`linear_attention`/Gated DeltaNet and 16 `full_attention`), hidden size 5,120,
FFN size 17,408, 24 query heads, 4 KV heads, 256 head dimension, a 64-d rotary
slice (`partial_rotary_factor=0.25`), `rope_theta=10,000,000`, and
`mrope_section=[11,11,10]`. The model declares one MTP hidden layer and no
dedicated MTP embeddings. See `docs/RESEARCH.md` and
`scripts/inspect_model.py` for the evidence.

## Quick start

```bash
cd /root/qwen/brainwaves-longwriter-bench
python3 scripts/inspect_model.py --model-dir /models/Qwen3.8-27B-Brainwaves
./scripts/inspect_system.sh

# Native reference (BF16 weights, BF16 KV, text-only)
PROFILE=native-262k ./serving/vllm/start.sh

# Separate processes are intentional: static YaRN×4 should not affect short prompts.
PROFILE=yarn-512k ./serving/vllm/start.sh
PROFILE=yarn-1m ./serving/vllm/start.sh
```

The launcher uses the ROCm container and exposes an OpenAI-compatible API on
`127.0.0.1:8000`. Set `VLLM_API_KEY` or `API_KEY_FILE` before exposing it beyond
localhost. `DRY_RUN=1` prints the exact command without starting a container.

Download a pinned revision on another machine with:

```bash
python3 scripts/download_model.py \
  --repo-id nightmedia/Qwen3.8-27B-Brainwaves \
  --revision f9545772aab3abcb84b2f1822134a1c4a052669f \
  --local-dir /models/Qwen3.8-27B-Brainwaves
```

## Arro LongWriter Bench

All story prose is newly generated for this repository. The benchmark premise
uses only the high-level setting and character names supplied for this test; it
does not copy manga, anime, novel, subtitle, scanlation, wiki, or fan-translation
text. `gold_state/` stores event-backed truth, per-character knowledge, and
relationship dimensions.

```bash
# Validate fixtures without contacting a model
python3 benchmarks/arro_longwriter/generate_fixtures.py --validate

# Run identical nested fixtures against the active endpoint
python3 benchmarks/arro_longwriter/run.py \
  --base-url http://127.0.0.1:8000 \
  --model brainwaves \
  --lengths 8192,32768,65536,131072,262144 \
  --scenarios all \
  --output results/raw/native-262k.jsonl

# Score machine checks and emit a reviewable report
python3 benchmarks/arro_longwriter/score.py \
  --input results/raw/native-262k.jsonl \
  --output results/aggregate/native-262k.json \
  --markdown reports/262k.md
```

The full requested matrix is 8K, 16K, 32K, 64K, 128K, 192K, 256K, 384K,
512K, 768K, and ~1M, with repeated seeds and long-output targets. Use
`scripts/benchmark_all.sh` to run a bounded matrix; set `ALLOW_ULTRA=1` only
after the 262K control is healthy. Long outputs are scored for loops, voice
convergence, POV/tense drift, premature resolution, knowledge leakage,
relationship resets, and callback naturalness. Subjective prose scores are
blinded and may be supplied by multiple judge providers; Brainwaves is never its
own sole judge.

## Runtime comparisons

vLLM V1 is the first measured path. `serving/sglang/start.sh` is a pinned,
reproducible comparison path for the SGLang main commit documented by its Qwen
3.8 recipe; SGLang is not silently reported as benchmarked until its container
is installed and the checkpoint boots correctly on this ROCm host. MTP,
prefix caching, chunked prefill, AITER, and FP8 KV are independent A/B variables.

## Reports and release hygiene

`reports/environment.{json,md}` records the host and container audit;
`reports/memory_model.md` derives the hybrid KV/state memory; and
`reports/FINAL_REPORT.md` is the decision record. `docs/RESEARCH.md` contains
dated primary-source links. Model weights and credentials are excluded by
`.gitignore`. The public repository should contain concise summaries and
reproduction commands, not million-token traces or private story text.

## Acknowledgement

This project gratefully acknowledges the AI Developer Program for providing
access to the AMD Instinct MI300X GPU used for the serving, benchmarking, and
long-context evaluation work.
