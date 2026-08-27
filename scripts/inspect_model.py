#!/usr/bin/env python3
"""Inspect config/tokenizer/weights without loading model weights into VRAM."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while data := fh.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()


def safetensor_header(path: Path) -> tuple[int, str | None]:
    import struct

    with path.open("rb") as fh:
        raw = fh.read(8)
        if len(raw) != 8:
            return 0, None
        length = struct.unpack("<Q", raw)[0]
        header = json.loads(fh.read(length))
    params = 0
    dtypes: set[str] = set()
    for key, value in header.items():
        if key == "__metadata__":
            continue
        shape = value.get("shape", [])
        n = 1
        for dim in shape:
            n *= int(dim)
        params += n
        dtypes.add(str(value.get("dtype")))
    return params, ",".join(sorted(dtypes)) if dtypes else None


def revision_from_cache(model_dir: Path) -> str | None:
    for path in sorted((model_dir / ".cache/huggingface/download").glob("config.json.metadata")):
        lines = path.read_text().splitlines()
        if lines:
            return lines[0]
    return os.getenv("MODEL_REVISION")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default=os.getenv("MODEL_DIR", "/models/Qwen3.8-27B-Brainwaves"))
    ap.add_argument("--repo-id", default="nightmedia/Qwen3.8-27B-Brainwaves")
    ap.add_argument("--revision", default=None)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    root = Path(args.model_dir)
    config = json.loads((root / "config.json").read_text())
    text = config.get("text_config", config)
    layer_types = text.get("layer_types", [])
    weight_files = sorted(root.glob("*.safetensors"))
    param_count = 0
    dtype_counts: dict[str, int] = {}
    for path in weight_files:
        count, dtype = safetensor_header(path)
        param_count += count
        if dtype:
            for item in dtype.split(","):
                dtype_counts[item] = dtype_counts.get(item, 0) + count
    small_files = {}
    for name in ["config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "generation_config.json", "model.safetensors.index.json"]:
        path = root / name
        if path.exists():
            small_files[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    license_value = None
    readme = root / "README.md"
    if readme.exists():
        for line in readme.read_text(errors="replace").splitlines()[:40]:
            if line.lower().startswith("license:"):
                license_value = line.split(":", 1)[1].strip()
                break
    result = {
        "repo_id": args.repo_id,
        "revision": args.revision or revision_from_cache(root),
        "model_dir": str(root),
        "architecture": config.get("architectures"),
        "model_type": config.get("model_type"),
        "language_model_only": config.get("language_model_only"),
        "license_metadata": license_value,
        "parameter_count": param_count,
        "parameter_count_billions": round(param_count / 1e9, 6) if param_count else None,
        "weight_dtype_counts": dtype_counts,
        "weight_files": [{"name": p.name, "bytes": p.stat().st_size} for p in weight_files],
        "weight_bytes": sum(p.stat().st_size for p in weight_files),
        "text_config": {
            "hidden_size": text.get("hidden_size"),
            "intermediate_size": text.get("intermediate_size"),
            "num_hidden_layers": text.get("num_hidden_layers"),
            "num_attention_heads": text.get("num_attention_heads"),
            "num_key_value_heads": text.get("num_key_value_heads"),
            "head_dim": text.get("head_dim"),
            "max_position_embeddings": text.get("max_position_embeddings"),
            "layer_types": layer_types,
            "linear_attention_layers": layer_types.count("linear_attention"),
            "full_attention_layers": layer_types.count("full_attention"),
            "linear_num_key_heads": text.get("linear_num_key_heads"),
            "linear_num_value_heads": text.get("linear_num_value_heads"),
            "linear_key_head_dim": text.get("linear_key_head_dim"),
            "linear_value_head_dim": text.get("linear_value_head_dim"),
            "partial_rotary_factor": text.get("partial_rotary_factor"),
            "rope_parameters": text.get("rope_parameters"),
            "mtp_num_hidden_layers": text.get("mtp_num_hidden_layers"),
            "mtp_use_dedicated_embeddings": text.get("mtp_use_dedicated_embeddings"),
            "mamba_ssm_dtype": text.get("mamba_ssm_dtype"),
        },
        "small_file_hashes": small_files,
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
