#!/usr/bin/env python3
"""Exercise planner → simulator → writer → auditor → reviser on one server."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import requests


def call(url: str, model: str, task: str, seed: int, max_tokens: int) -> dict:
    body = {"model": model, "messages": [{"role": "user", "content": task}],
            "max_tokens": max_tokens, "temperature": 0.65, "top_p": 0.9,
            "top_k": 20, "presence_penalty": 1.0, "seed": seed,
            "chat_template_kwargs": {"enable_thinking": False}}
    start = time.perf_counter(); r = requests.post(url.rstrip("/") + "/v1/chat/completions", json=body, timeout=(60, 7200)); r.raise_for_status()
    d = r.json(); msg = (d.get("choices") or [{}])[0].get("message") or {}
    return {"text": msg.get("content") or "", "usage": d.get("usage") or {}, "elapsed_s": time.perf_counter() - start}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--base-url", default="http://127.0.0.1:8000"); ap.add_argument("--model", default="brainwaves-qwen38-27b"); ap.add_argument("--max-tokens", type=int, default=256); ap.add_argument("--output", default="results/aggregate/standalone-loop.json"); args = ap.parse_args()
    state = "Arro sincerely prioritizes Minami's happiness, while Akari, Shiori, and Minami retain independent agency."
    roles = ["planner", "scene_architect", "character_simulator", "writer", "continuity_auditor", "reviser"]
    rows = []
    for i, role in enumerate(roles):
        task = f"Act as the {role} for one original school-romcom scene. Preserve this persistent state:\n{state}\nReturn concise useful work for the next role; do not cite source material."
        result = call(args.base_url, args.model, task, 2000 + i, args.max_tokens); result.update({"role": role}); rows.append(result)
        state += "\n" + result["text"][-1500:]
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps({"roles": rows, "persistent_state_chars": len(state)}, indent=2, ensure_ascii=False) + "\n"); print(out); return 0


if __name__ == "__main__": raise SystemExit(main())
