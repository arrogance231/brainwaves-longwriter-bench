# Brainwaves hybrid memory model

Model weights: 55,563,007,176 bytes (51.75 GiB) from safetensors.

## Formula

Full-attention KV bytes/token = full_layers × KV_heads × head_dim × K/V(2) × bytes = 16 × 4 × 256 × 2 × bytes.

The 48 GDN layers use a recurrent state rather than a full-history KV. The SGLang Qwen3.8 recipe reports one recurrent state slot as 153.9 MB FP32 or 78.4 MB BF16; the checkpoint declares `mamba_ssm_dtype=float32`, so FP32 is the conservative default. State slots, scheduler buffers, graph memory, and fragmentation are workload-dependent and must be measured.

## Full-attention KV by active context

| Context | BF16 KV | FP8 KV | Weight + BF16 KV | Weight + FP8 KV |
|---:|---:|---:|---:|---:|
| 262,144 | 16.00 GiB | 8.00 GiB | 67.75 GiB | 59.75 GiB |
| 524,288 | 32.00 GiB | 16.00 GiB | 83.75 GiB | 67.75 GiB |
| 1,010,000 | 61.65 GiB | 30.82 GiB | 113.39 GiB | 82.57 GiB |

## Recurrent state sensitivity

| State dtype | One slot | 4 slots | 8 slots |
|---|---:|---:|---:|
| FP32 (checkpoint declaration) | 153.9 MB | 615.6 MB | 1.23 GB |
| BF16 (experimental) | 78.4 MB | 313.6 MB | 627.2 MB |

## Interpretation

At 1,010,000 tokens, the measured weight file plus full-attention BF16 KV is 113.39 GiB before activations, graph capture, recurrent state slots, prefix-cache duplication, and allocator safety margin. It fits numerically below a 192 GiB MI300X, but this is not a runtime guarantee: the 1M server must be booted and prefilling measured. A BF16 KV control is required before enabling FP8; FP8 saves half of full-attention KV but does not remove GDN state or activation costs.
