# Brainwaves MI300X final report

Captured 2026-08-27. This decision record separates what loaded from what was
actually usable. A context window is not promoted by a successful server start
alone.

## Model

| Field | Value |
|---|---|
| Model | `nightmedia/Qwen3.8-27B-Brainwaves` |
| Revision | `f9545772aab3abcb84b2f1822134a1c4a052669f` |
| Weights | BF16 safetensors, 55,563,007,176 bytes (51.75 GiB) |
| Parameters | 27,781,427,952 |
| Native context | 262,144 |
| Architecture | `Qwen3_5ForConditionalGeneration`; 48 Gated DeltaNet/linear-attention + 16 full-attention layers |
| Attention | 24 Q heads, 4 KV heads, head dimension 256, partial RoPE 0.25 |

The display name says Qwen3.8, but the pinned config is the Qwen3.5 hybrid
architecture. The config, not the display name, is the source of truth.

## System

| Component | Recorded value |
|---|---|
| GPU | AMD Instinct MI300X VF, `gfx942`, 205,822,885,888 bytes VRAM |
| Host | Linux kernel `7.0.0-27-generic`, one NUMA node, 235 GiB RAM, no swap |
| ROCm/HIP | ROCm userspace 7.2.3; HIP `7.2.53211` |
| PyTorch | `2.12.0+git6bbd260` |
| Transformers | `5.16.1` |
| vLLM | `0.28.0` ROCm image `vllm-rocm:0.28.0-gfx942` |
| AITER | Installed; tested on/off |
| SGLang | Not executable: available Qwen3.8 image is CUDA-only (`torch.version.hip=None`) |

## Context results

| Context/profile | Loads | Retrieval/continuity | Narrative quality | Stability | Classification |
|---|---|---|---|---|---|
| 262K native, BF16 KV | Yes | 3/3 long-prompt machine checks passed; 1.000 continuity on the 232K-token fixture | Subjective review pending; no n-gram repetition or leakage in pilot | Completed 3 non-stream requests, 259–290 s end-to-end each | **USABLE** for offline/rare long audits; too slow for default interactive work |
| 512K YaRN×2, BF16 KV | Yes | No completion; no score | Not measurable | No first token in ~540 s; VRAM ~182.0 GB; GPU 100% | **EXPERIMENTAL / FAILED pilot** |
| 1.01M YaRN×4, BF16 KV | Yes | No completion; no score | Not measurable | No first token in ~300 s; VRAM ~184.0 GB; GPU 100% | **EXPERIMENTAL / FAILED pilot** |

The native 262K quality run is a small machine-check pilot, not a claim of
human-level narrative validation. The 512K and 1M results are honest bounded
pilot failures, not quality passes.

## Performance

The corrected BF16 normal-decode run used 128 output tokens (or the model's
natural stop) and an 8,192-token chunk budget:

| Target context | Prompt tokens | Prefill tok/s | Decode tok/s | TTFT | Elapsed |
|---:|---:|---:|---:|---:|---:|
| 8K | 7,277 | 2,362 | 35.11 | 3.08 s | 6.73 s |
| 32K | 28,947 | 5,381 | 14.28 | 5.38 s | 14.34 s |
| 64K | 57,849 | 4,396 | 8.04 | 13.16 s | 25.85 s |
| 128K | 116,081 | 2,492 | 4.34 | 46.58 s | 56.73 s |

An additional native 262K quality fixture contained 232,846–232,858 actual
prompt tokens and completed in 259–290 s. It demonstrates operation, but its
non-stream response does not expose a reliable decode timestamp.

### A/B results

* FP8 E4M3 KV doubled vLLM's reported native cache capacity from roughly 1.80M
  to 3.53M cache tokens. On the 8K/32K quality pilot, BF16 and FP8 had the same
  deterministic continuity (0.833), zero leakage, and zero measured 5-gram
  repetition. FP8 is an optional capacity profile, not the quality reference;
  it was not yet re-run at 262K.
* AITER on and off were effectively tied in the short throughput sample:
  8K 35.11 vs 35.13 decode tok/s, and 32K 14.28 vs 14.29. Keep AITER enabled
  for the tested image, but do not claim a speedup. The image logged a ROCm
  compiler-option warning and used fallbacks for some kernels.
* Native MTP (`num_speculative_tokens=2`) reached 45.57 decode tok/s versus
  34.18 tok/s in the comparable short FP8 normal-decode probe, with 156/334
  draft tokens accepted (46.7%). It is experimental on AMD; vLLM rejects
  `min_p` with this path and a longer quality comparison is still required.
* Automatic prefix caching is enabled. A repeated 32K prompt measured 9.61 s
  cold versus 3.47 s warm in the captured run; vLLM metrics exposed cache-hit
  counters. The exact cache gain is workload-dependent.
* Chunked prefill is enabled through vLLM's `--max-num-batched-tokens 8192`.
  This image does not accept a separate chunk-size flag.
* Paged KV, continuous batching, and the launcher hooks for KV offload are
  present. CPU/NVMe offload was not promoted: it was not measured as a stable
  native path in this run.

## Writing/endurance probes

The 5K-word target naturally stopped at 2,533 tokens/1,839 words in 79.54 s at
31.89 decode tok/s. That is a measured rate of approximately 1,389 words/min;
extrapolating the same rate gives about 3.6 minutes for 5,000 words, but the
model did not itself complete a 5K-word request. A three-chapter persistent
state smoke run completed; the requested 20/50-chapter endurance suite and
blinded prose judging remain future work. The standalone planner → scene
architect → simulator → writer → auditor → reviser loop is implemented and was
smoke-tested, but its outputs were not independently human-rated.

## Memory model

Because only 16 layers retain ordinary full-attention KV, the derived KV cost is
65,536 bytes/token in BF16 and 32,768 bytes/token in FP8. Approximate full-KV
capacity costs are:

| Context | BF16 KV | FP8 KV |
|---:|---:|---:|
| 262K | 16.0 GiB | 8.0 GiB |
| 512K | 32.0 GiB | 16.0 GiB |
| 1.01M | 61.65 GiB | 30.82 GiB |

Weights use 51.75 GiB; GDN recurrent state, graphs, workspaces, fragmentation,
and safety headroom must be added. The 1M BF16 arithmetic fits under 192 GiB on
paper, but the pilot shows that HBM fit does not imply acceptable time-to-first
token.

## Final recommendation

* **Best default context:** 32K–64K native BF16, where interactive decode is
  8–35 tok/s and prefix reuse is practical.
* **Best maximum reliable context:** native 262K for offline/rare continuity
  audits, with very high end-to-end latency; do not use it as the everyday
  profile.
* **Experimental maximum:** 1.01M YaRN×4 (launchable only; failed bounded
  first-token pilot).
* **Recommended KV dtype:** BF16 for the reference; FP8 E4M3 as an opt-in
  capacity experiment after a 262K quality A/B.
* **Recommended runtime:** vLLM V1 ROCm 0.28.0 for this host. SGLang is not
  included in the performance comparison because the available image is CUDA
  only and did not boot HIP.
* **MTP:** promising short-run speed benefit, but experimental on AMD and not
  yet quality-qualified for long writing.
* **Long-context LoRA required:** not justified yet. First fix the 512K/1M
  prefill bottleneck and complete the narrative degradation curves; do not
  train against an unmeasured failure mode.
* **Standalone Story OS verdict:** **NO** at this evidence level. Brainwaves can
  serve as a capable single-model writer/planner loop at native contexts, but
  this run does not prove that it can replace separate continuity/prose models
  at 512K/1M, and the long-context quality/endurance gates are incomplete.

## Reproduction and release

Use the pinned model revision and commands in the root README. The repository
contains no model weights, HF credentials, or copyrighted source passages. It
includes the AI Developer Program acknowledgement for the MI300X access.
