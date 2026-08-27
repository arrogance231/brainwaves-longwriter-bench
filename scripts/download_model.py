#!/usr/bin/env python3
"""Download and attest one immutable Hugging Face model revision."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while data := fh.read(chunk):
            h.update(data)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", default=os.getenv("MODEL_ID", "nightmedia/Qwen3.8-27B-Brainwaves"))
    ap.add_argument("--revision", default=os.getenv("MODEL_REVISION", "f9545772aab3abcb84b2f1822134a1c4a052669f"))
    ap.add_argument("--local-dir", default=os.getenv("MODEL_DIR", "/models/Qwen3.8-27B-Brainwaves"))
    ap.add_argument("--manifest", default=None, help="Write a JSON manifest beside the model")
    args = ap.parse_args()

    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError as exc:
        raise SystemExit("Install huggingface_hub (or run this script in the vLLM container).") from exc

    model_dir = Path(args.local_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=args.repo_id,
        revision=args.revision,
        local_dir=str(model_dir),
        token=os.getenv("HF_TOKEN") or None,
    )
    info = HfApi().model_info(args.repo_id, revision=args.revision, token=os.getenv("HF_TOKEN") or None)
    files = []
    for path in sorted(model_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        item = {"name": path.name, "bytes": path.stat().st_size}
        if path.stat().st_size <= 64 * 1024 * 1024:
            item["sha256"] = sha256(path)
        files.append(item)
    manifest = {
        "repo_id": args.repo_id,
        "revision": args.revision,
        "resolved_sha": getattr(info, "sha", args.revision),
        "last_modified": getattr(info, "lastModified", None),
        "local_dir": str(model_dir),
        "files": files,
    }
    output = Path(args.manifest) if args.manifest else model_dir / "download-manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
