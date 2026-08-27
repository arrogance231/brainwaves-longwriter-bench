# Known issues

* This Brainwaves merge declares the Qwen3.5 architecture key despite the
  Qwen3.8 name. Always use the downloaded `config.json`, not assumptions from
  the display name.
* Static YaRN is profile-wide. Do not run factor 4 for short prompts; route to
  the native process instead.
* vLLM's Qwen3.5 recipe marks MTP-1 on AMD under development. MTP remains opt-in
  and must be compared against normal decoding for quality and acceptance rate.
* Hybrid GDN cache sizing and CUDA-graph capture can fail when the capture batch
  exceeds recurrent cache slots. The launcher exposes
  `MAX_CUDAGRAPH_CAPTURE_SIZE` for controlled reduction.
* FP8 KV scale calibration is not enabled by default. A BF16-KV control is
  mandatory before any FP8 quality conclusion.
* AITER may compile or select different kernels by image/runtime. A speedup
  without an output-quality check is not accepted.
* No SGLang result is claimed until the documented mainline commit is installed
  in a ROCm-compatible container and serves this exact revision.
* On this host the available `lmsysorg/sglang:dev-qwen38-dflash2` image is
  CUDA-only (`torch.version.hip=None`) and cannot boot on the MI300X. It is
  recorded as unavailable rather than silently compared against vLLM.
* A single 524K YaRN×2 BF16 request used 100% GPU and produced no first token in
  roughly nine minutes. A single 1.01M YaRN×4 request behaved similarly for a
  five-minute bounded pilot. These are prefill/runtime failures, not quality
  passes; reduce the prefill bottleneck before attempting LoRA training.
* The ROCm image falls back to Triton for some GDN decode and paged-attention
  paths, and emits an unsupported clang option warning while compiling AITER.
  This explains why the measured AITER on/off short samples were effectively
  tied and is a candidate for future kernel work.
