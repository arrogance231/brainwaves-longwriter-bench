#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

from benchmarks.arro_longwriter.fixtures.common import build_fixture


def one(base_url: str, model: str, prompt: str, output_tokens: int, seed: int, timeout: float, *, speculative: bool = False) -> dict:
    started = time.perf_counter(); first = None; text = []; usage = {}
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": output_tokens, "temperature": 0.8, "top_p": 0.9, "top_k": 20, "presence_penalty": 1.2, "seed": seed, "stream": True, "stream_options": {"include_usage": True}, "chat_template_kwargs": {"enable_thinking": False}}
    # vLLM currently rejects min_p with speculative decoding.  Keep the
    # normal creative profile unchanged, but make the MTP comparison runnable.
    if not speculative:
        body["min_p"] = 0.05
    try:
        r = requests.post(base_url.rstrip("/") + "/v1/chat/completions", json=body, stream=True, timeout=(60, timeout)); r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"): continue
            payload=line[5:].strip()
            if payload == "[DONE]": continue
            try: chunk=json.loads(payload)
            except json.JSONDecodeError: continue
            if first is None: first=time.perf_counter()
            usage.update(chunk.get("usage") or {})
            for choice in chunk.get("choices") or []:
                delta=choice.get("delta") or {}
                if delta.get("content"): text.append(delta["content"])
        ended=time.perf_counter(); completion=int(usage.get("completion_tokens") or len("".join(text).split()))
        return {"ok":True,"prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":completion,"elapsed_s":ended-started,"ttft_s":(first-started if first else ended-started),"decode_tok_s":completion/max(ended-(first or ended),1e-6),"prefill_tok_s":(usage.get("prompt_tokens") or 0)/max((first-started if first else ended-started),1e-6),"usage":usage}
    except Exception as e:
        return {"ok":False,"error":repr(e),"elapsed_s":time.perf_counter()-started}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://127.0.0.1:8000"); ap.add_argument("--model",default="brainwaves-qwen38-27b"); ap.add_argument("--context-lengths",default="8192,32768,65536,131072,262144"); ap.add_argument("--output-tokens",type=int,default=256); ap.add_argument("--requests",type=int,default=1); ap.add_argument("--timeout",type=float,default=7200); ap.add_argument("--speculative",action="store_true",help="omit min_p for an MTP/speculative server"); ap.add_argument("--output",default="results/aggregate/throughput.json")
    args=ap.parse_args(); rows=[]
    for length in [int(x) for x in args.context_lengths.split(",") if x]:
        prompt=build_fixture(length,"narrative_continuation",101,0)["prompt"]
        for i in range(args.requests):
            row=one(args.base_url,args.model,prompt,args.output_tokens,101+i,args.timeout,speculative=args.speculative); row.update({"context_target_tokens":length,"request":i}); rows.append(row); print(json.dumps(row),flush=True)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps({"runtime":{"base_url":args.base_url,"model":args.model},"rows":rows},indent=2)+"\n"); return 0


if __name__=="__main__": raise SystemExit(main())
