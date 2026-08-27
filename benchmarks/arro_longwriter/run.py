#!/usr/bin/env python3
"""Run nested Arro fixtures through an OpenAI-compatible endpoint."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.arro_longwriter.fixtures.common import SCENARIOS, build_fixture


def call(base_url: str, model: str, prompt: str, seed: int, max_tokens: int, sampling: dict, timeout: float, *, stream: bool = True) -> dict:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "seed": seed,
        "temperature": sampling.get("temperature", 0.8),
        "top_p": sampling.get("top_p", 0.9),
        "top_k": sampling.get("top_k", 20),
        "min_p": sampling.get("min_p", 0.05),
        "presence_penalty": sampling.get("presence_penalty", 1.2),
        "repetition_penalty": sampling.get("repetition_penalty", 1.0),
        "stream": stream,
        **({"stream_options": {"include_usage": True}} if stream else {}),
        # vLLM exposes chat_template_kwargs as a request field (not nested
        # under extra_body).  Keeping this at the top level is important for
        # Brainwaves: otherwise the model silently spends the whole budget in
        # its reasoning channel and emits no prose.
        "chat_template_kwargs": {"enable_thinking": bool(sampling.get("thinking", False))},
    }
    started = time.perf_counter()
    first = None
    text_parts: list[str] = []
    usage = {}
    try:
        response = requests.post(url, json=body, stream=True, timeout=(60, timeout))
        response.raise_for_status()
        if stream:
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    continue
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if first is None:
                    first = time.perf_counter()
                usage.update(chunk.get("usage") or {})
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    if delta.get("content"):
                        text_parts.append(delta["content"])
        else:
            payload = response.json()
            first = time.perf_counter()
            usage.update(payload.get("usage") or {})
            choices = payload.get("choices") or []
            if choices:
                text_parts.append((choices[0].get("message") or {}).get("content") or "")
        ended = time.perf_counter()
        elapsed = ended - started
        text = "".join(text_parts)
        completion_tokens = int(usage.get("completion_tokens") or max(1, len(text.split())))
        return {
            "ok": True,
            "response": text,
            "usage": usage,
            "elapsed_s": elapsed,
            "ttft_s": (first - started) if first else elapsed,
            "completion_tokens": completion_tokens,
            # Non-streaming responses expose no token timestamps; do not
            # manufacture a decode rate from a zero-length interval.
            "decode_tok_s": (completion_tokens / max(ended - first, 1e-6)) if stream and first else None,
            "stream": stream,
            "error": None,
        }
    except Exception as exc:
        return {"ok": False, "response": "", "usage": usage, "elapsed_s": time.perf_counter() - started, "ttft_s": None, "completion_tokens": 0, "decode_tok_s": None, "error": repr(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="brainwaves-qwen38-27b")
    ap.add_argument("--lengths", default="8192,16384,32768,65536,131072,196608,262144,393216,524288,768000,1010000")
    ap.add_argument("--scenarios", default="all")
    ap.add_argument("--seeds", default="101,202,303")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=float, default=7200)
    ap.add_argument("--no-stream", action="store_true", help="use JSON responses for very long prompts when a streaming connection does not close cleanly")
    ap.add_argument("--output", default="results/raw/arro.jsonl")
    ap.add_argument("--sampling", default="normal-prose", choices=["deterministic-continuity", "normal-prose", "dialogue", "planning", "revision"])
    args = ap.parse_args()
    sampling_defaults = {
        "deterministic-continuity": {"temperature": 0.6, "top_p": 0.85, "top_k": 20, "min_p": 0, "presence_penalty": 1.0, "thinking": False},
        "normal-prose": {"temperature": 0.8, "top_p": 0.9, "top_k": 20, "min_p": 0.05, "presence_penalty": 1.2, "thinking": False},
        "dialogue": {"temperature": 0.85, "top_p": 0.9, "top_k": 20, "min_p": 0.05, "presence_penalty": 1.0, "thinking": False},
        "planning": {"temperature": 0.7, "top_p": 0.85, "top_k": 20, "min_p": 0.05, "presence_penalty": 1.2, "thinking": True},
        "revision": {"temperature": 0.6, "top_p": 0.85, "top_k": 20, "min_p": 0.05, "presence_penalty": 1.4, "thinking": False},
    }
    lengths = [int(x) for x in args.lengths.split(",") if x]
    scenarios = list(SCENARIOS) if args.scenarios == "all" else [x for x in args.scenarios.split(",") if x]
    seeds = [int(x) for x in args.seeds.split(",") if x]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    total = len(lengths) * len(scenarios) * len(seeds) * args.samples
    done = 0
    with output.open("w") as fh:
        for length in lengths:
            for seed in seeds:
                for scenario in scenarios:
                    for sample in range(args.samples):
                        fixture = build_fixture(length, scenario, seed, sample)
                        result = call(args.base_url, args.model, fixture["prompt"], seed + sample, args.max_tokens, sampling_defaults[args.sampling], args.timeout, stream=not args.no_stream)
                        row = {k: v for k, v in fixture.items() if k != "prompt"}
                        row.update(result)
                        row["runtime"] = {"base_url": args.base_url, "model": args.model, "sampling": args.sampling}
                        fh.write(json.dumps(row, sort_keys=True) + "\n")
                        fh.flush()
                        done += 1
                        print(f"[{done}/{total}] {length} {scenario} seed={seed} ok={result['ok']} elapsed={result['elapsed_s']:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
