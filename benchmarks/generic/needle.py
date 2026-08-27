#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://127.0.0.1:8000"); ap.add_argument("--model",default="brainwaves-qwen38-27b"); ap.add_argument("--length",type=int,default=8192); ap.add_argument("--position",type=float,default=0.5); ap.add_argument("--output",default="results/aggregate/needle.json"); args=ap.parse_args()
    chars=args.length*4; at=max(0,min(chars-1,int(chars*args.position))); filler="A quiet original paragraph describes a school day and a small unresolved choice. "
    body=(filler*((chars//len(filler))+2))[:at]+"\nNEEDLE: The brass compass is inside locker 417.\n"+(filler*((chars//len(filler))+2)); body=body[:chars]
    prompt=f"Read the original synthetic story below. Where is the brass compass? Answer exactly, then write one sentence.\n\n{body}"
    t=time.perf_counter(); r=requests.post(args.base_url.rstrip("/")+"/v1/chat/completions",json={"model":args.model,"messages":[{"role":"user","content":prompt}],"max_tokens":64,"temperature":0.6,"top_p":0.85,"top_k":20,"presence_penalty":1.0,"seed":101,"extra_body":{"chat_template_kwargs":{"enable_thinking":False}}},timeout=(60,7200)); elapsed=time.perf_counter()-t; r.raise_for_status(); data=r.json(); text=data["choices"][0]["message"].get("content",""); out={"target_tokens":args.length,"position":args.position,"found":"locker 417" in text.lower() and "brass compass" in text.lower(),"response":text,"elapsed_s":elapsed,"usage":data.get("usage")}; Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
