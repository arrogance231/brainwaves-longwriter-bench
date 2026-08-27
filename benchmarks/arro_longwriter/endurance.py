#!/usr/bin/env python3
"""Persistent multi-chapter endurance probe using one Brainwaves endpoint.

The script deliberately carries a compact state ledger and the prior chapter
forward; it never resets the conversation between chapters.  It is bounded by
default so a public CI checkout cannot accidentally launch a 20-chapter GPU
run.  Set --chapters 20 (or 50) for the full local study.
"""
from __future__ import annotations

import argparse, json, time
from pathlib import Path
import requests

from benchmarks.arro_longwriter.fixtures.common import build_story


def generate(url: str, model: str, prompt: str, max_tokens: int, seed: int, timeout: float) -> dict:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.8, "top_p": 0.9,
            "top_k": 20, "min_p": 0.05, "presence_penalty": 1.2,
            "seed": seed, "chat_template_kwargs": {"enable_thinking": False}}
    started = time.perf_counter()
    response = requests.post(url.rstrip("/") + "/v1/chat/completions", json=body,
                              timeout=(60, timeout))
    response.raise_for_status()
    data = response.json(); elapsed = time.perf_counter() - started
    msg = (data.get("choices") or [{}])[0].get("message") or {}
    return {"text": msg.get("content") or "", "usage": data.get("usage") or {},
            "elapsed_s": elapsed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="brainwaves-qwen38-27b")
    ap.add_argument("--chapters", type=int, default=3)
    ap.add_argument("--chapter-tokens", type=int, default=256)
    ap.add_argument("--context-tokens", type=int, default=32768)
    ap.add_argument("--output", default="results/raw/arro-endurance.jsonl")
    args = ap.parse_args()
    state = "Arro's friend-first premise is active. No relationship resets are allowed."
    previous = build_story(args.context_tokens, 101)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for chapter in range(1, args.chapters + 1):
            prompt = ("You are continuing an original synthetic AU. Preserve the event-backed state, "
                      "knowledge boundaries, emotional residue, POV, and slow-burn pacing.\n\n"
                      f"PERSISTENT STATE:\n{state}\n\nPREVIOUS MATERIAL:\n{previous[-120000:]}\n\n"
                      f"Write chapter {chapter}; advance one unresolved thread without resolving the romance instantly.")
            result = generate(args.base_url, args.model, prompt, args.chapter_tokens, 1000 + chapter, 7200)
            text = result["text"]
            state = state + f"\nChapter {chapter} committed; unresolved threads remain.\n" + text[-2000:]
            previous = text
            row = {"chapter": chapter, "ok": True, **result,
                   "state_chars": len(state), "runtime": {"model": args.model}}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n"); fh.flush(); print(json.dumps({k: row[k] for k in ("chapter", "elapsed_s", "usage")}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
