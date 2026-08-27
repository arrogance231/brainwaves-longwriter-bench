# Reproducibility

Record the following with every run:

* git commit and model revision;
* image digest/name, vLLM/SGLang, Transformers, PyTorch, ROCm, HIP, AITER;
* GPU, HBM, driver/kernel, CPU/RAM/NUMA, and disk;
* profile, YaRN override, weight/KV dtype, MTP/AITER/cache/chunk settings;
* fixture revision, lengths, seeds, sampling values, output cap, and concurrency;
* TTFT, prefill/decode tok/s, ITL, HBM/KV/state/cache counters, failures, and
  quality artifacts.

`scripts/inspect_system.sh` and `scripts/inspect_model.py` produce machine-
readable records. The public repository keeps summaries and safe blinded
artifacts; million-token prompts, private story text, raw responses, and
unblinded mappings belong in local or release artifacts.
