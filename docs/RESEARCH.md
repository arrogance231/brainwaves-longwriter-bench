# Research record

Research was retrieved on **2026-08-27**. Links below are primary model/runtime
sources where available; local observations are marked as such.

## Brainwaves checkpoint

* The [Brainwaves model card](https://huggingface.co/nightmedia/Qwen3.8-27B-Brainwaves)
  declares Apache-2.0 metadata, BF16 safetensors, an experimental merge, and
  `image-text-to-text`/`qwen3_5` tags. Its merge recipe and long-context tags
  are creator claims, not independent quality evidence.
* The Hugging Face API reported HEAD revision
  `f9545772aab3abcb84b2f1822134a1c4a052669f`, last modified 2026-08-25. That
  revision is pinned by this project and downloaded to a separate model path.
* The actual local config at that revision declares
  `Qwen3_5ForConditionalGeneration`, 64 text layers, 48 linear-attention and 16
  full-attention layers, 24/4 attention heads, 256 head dimension, partial RoPE
  factor 0.25, `rope_theta=10000000`, `mrope_section=[11,11,10]`, native
  `max_position_embeddings=262144`, and `mtp_num_hidden_layers=1`.
  Safetensor inspection counted 27,781,427,952 BF16 parameters. The model card's
  28B display is consistent after rounding.
* The checkpoint config's `model_name` is `unsloth/Qwen3.8-27B` while its
  architecture key is `qwen3_5`. This repository follows the actual config and
  does not assume the model name implies a different topology.

## Official Qwen guidance

* The [official Qwen3.5-27B model card](https://huggingface.co/Qwen/Qwen3.5-27B)
  (retrieved 2026-08-27) documents the same hybrid layout, 27B parameter scale,
  262,144 native context, and MTP trained with multiple steps. It recommends
  `--language-model-only` for text throughput and gives vLLM MTP as
  `{"method":"mtp","num_speculative_tokens":2}`.
* Its [ultra-long section](https://huggingface.co/Qwen/Qwen3.5-27B#processing-ultra-long-texts)
  says to use YaRN beyond native context, preserving
  `mrope_interleaved`, `mrope_section`, `rope_theta`, and
  `partial_rotary_factor`. It shows factor 4.0 for approximately 1.01M and
  explicitly says factor 2.0 is preferable when the typical context is 524,288.
  It warns that open-source runtimes implement static YaRN, which can degrade
  short prompts; this is why native, 512K, and 1M are separate processes.
* The [official Qwen3.8 repository](https://github.com/QwenLM/Qwen3.8), retrieved
  2026-08-27, describes Qwen3.8 as built on the Qwen3.5 hybrid architecture and
  links vLLM/SGLang recipes. The Brainwaves merge card is not an official Qwen
  checkpoint, so upstream capability claims do not transfer automatically.

## vLLM

* The [vLLM supported-model table](https://docs.vllm.ai/en/latest/models/supported_models/)
  lists `Qwen3_5ForConditionalGeneration` for text and experimental image/video
  inputs. The installed ROCm image is vLLM 0.28.0, newer than the earlier
  PaintedFantasy deployment and selected because its model registry includes
  this architecture.
* The [vLLM Qwen3.5 recipe](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html)
  (retrieved 2026-08-27) says AMD wheels require Python 3.12/ROCm 7 and supports
  MI300X/MI325X/MI355X. It recommends prefix caching, text-only mode for
  throughput, and notes that MTP-1 on AMD is still under development. It also
  documents a hybrid-cache CUDA-graph failure mode fixed by reducing
  `--max-cudagraph-capture-size` when the capture batch exceeds Mamba cache.
* The recipe calls prefix caching for Mamba align mode experimental. This project
  records prefix hit/reuse counters and treats them as a measurement, not a
  correctness assumption.
* The tested vLLM 0.28.0 ROCm image enables chunked prefill through
  `--enable-chunked-prefill`; it does not accept a separate
  `--chunked-prefill-size` flag, so `--max-num-batched-tokens` is the measured
  chunk-budget control for this build.

## SGLang

* The [SGLang Qwen3.8-27B cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)
  pins SGLang commit `1cf2b8c54d81802abc15dcf23a29b9cc687bc01e` for its recipe,
  describes the same 48-GDN/16-full hybrid, and exposes MTP/EAGLE settings. It
  reports 16 full-attention layers with 4 KV heads and recommends smaller
  chunked-prefill sizes for hybrid GDN decode interference.
* The cookbook's Mamba ratio formula uses 153.9 MB fp32 or 78.4 MB BF16 per
  recurrent state slot and 65.5 KB BF16 / 32.8 KB FP8 per full-attention KV
  token. Those values are used as a cross-check in `reports/memory_model.md`.
  SGLang is a comparison target, not declared faster until it boots and is
  benchmarked on this MI300X.

## ROCm / AMD

* The host audit reports MI300X VF `gfx942`, Linux kernel 7.0.0-27-generic, and
  ROCm SMI driver 7.0.0-27. The tested container uses ROCm 7.2.3 user space,
  PyTorch 2.12.0, HIP 7.2.53211, and AITER is installed in the image.
* AITER is tested through `VLLM_ROCM_USE_AITER=1` versus disabled. AITER is not
  considered correct solely because it is faster; corrupted output is a hard
  disable and goes to `docs/KNOWN_ISSUES.md`.

## Open questions

* Brainwaves is a creator merge, not a context-trained 1M checkpoint. The
  benchmark must establish whether YaRN preserves its writing behavior.
* FP8 KV and native MTP may have hybrid GDN-specific scale/cache interactions.
  BF16 KV and normal decoding remain the quality controls.
* No current SGLang container is installed on this host. The prepared launcher
  records the exact recipe and refuses to call an unverified comparison a
  result.
