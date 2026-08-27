#!/usr/bin/env python3
"""Derive hybrid full-attention KV and recurrent-state memory from config."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def gib(n: float) -> float:
    return n / 2**30


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--model-report",default="reports/model.json"); ap.add_argument("--output",default="reports/memory_model.md"); args=ap.parse_args()
    report=json.loads(Path(args.model_report).read_text()); c=report["text_config"]
    layers=int(c["full_attention_layers"]); kv_heads=int(c["num_key_value_heads"]); head_dim=int(c["head_dim"])
    weight_bytes=int(report["weight_bytes"])
    rows=[]
    for length in [262144,524288,1010000]:
        bf16=length*layers*kv_heads*head_dim*2*2
        fp8=length*layers*kv_heads*head_dim*2*1
        rows.append({"tokens":length,"bf16_bytes":bf16,"fp8_bytes":fp8,"bf16_gib":gib(bf16),"fp8_gib":gib(fp8)})
    md=["# Brainwaves hybrid memory model","",f"Model weights: {weight_bytes:,} bytes ({gib(weight_bytes):.2f} GiB) from safetensors.","", "## Formula", "", f"Full-attention KV bytes/token = full_layers × KV_heads × head_dim × K/V(2) × bytes = {layers} × {kv_heads} × {head_dim} × 2 × bytes.","", "The 48 GDN layers use a recurrent state rather than a full-history KV. The SGLang Qwen3.8 recipe reports one recurrent state slot as 153.9 MB FP32 or 78.4 MB BF16; the checkpoint declares `mamba_ssm_dtype=float32`, so FP32 is the conservative default. State slots, scheduler buffers, graph memory, and fragmentation are workload-dependent and must be measured.","", "## Full-attention KV by active context", "", "| Context | BF16 KV | FP8 KV | Weight + BF16 KV | Weight + FP8 KV |", "|---:|---:|---:|---:|---:|"]
    for r in rows: md.append(f"| {r['tokens']:,} | {r['bf16_gib']:.2f} GiB | {r['fp8_gib']:.2f} GiB | {gib(weight_bytes+r['bf16_bytes']):.2f} GiB | {gib(weight_bytes+r['fp8_bytes']):.2f} GiB |")
    md += ["", "## Recurrent state sensitivity", "", "| State dtype | One slot | 4 slots | 8 slots |", "|---|---:|---:|---:|", "| FP32 (checkpoint declaration) | 153.9 MB | 615.6 MB | 1.23 GB |", "| BF16 (experimental) | 78.4 MB | 313.6 MB | 627.2 MB |", "", "## Interpretation", "", f"At 1,010,000 tokens, the measured weight file plus full-attention BF16 KV is {gib(weight_bytes+rows[-1]['bf16_bytes']):.2f} GiB before activations, graph capture, recurrent state slots, prefix-cache duplication, and allocator safety margin. It fits numerically below a 192 GiB MI300X, but this is not a runtime guarantee: the 1M server must be booted and prefilling measured. A BF16 KV control is required before enabling FP8; FP8 saves half of full-attention KV but does not remove GDN state or activation costs.", ""]
    Path(args.output).write_text("\n".join(md)); print("wrote",args.output); return 0


if __name__=="__main__": raise SystemExit(main())
