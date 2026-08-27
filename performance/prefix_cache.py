#!/usr/bin/env python3
"""Run the same stable prefix twice and preserve cache counter evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from performance.throughput import one
from benchmarks.arro_longwriter.fixtures.common import build_fixture


def metrics(base_url: str) -> str:
    try: return subprocess.run(["curl","-fsS",base_url.rstrip("/")+"/metrics"],capture_output=True,text=True,timeout=20).stdout
    except Exception as e: return repr(e)


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://127.0.0.1:8000"); ap.add_argument("--model",default="brainwaves-qwen38-27b"); ap.add_argument("--length",type=int,default=32768); ap.add_argument("--output",default="results/aggregate/prefix-cache.json"); args=ap.parse_args()
    prompt=build_fixture(args.length,"narrative_continuation",101,0)["prompt"]; before=metrics(args.base_url); a=one(args.base_url,args.model,prompt,128,101,7200); b=one(args.base_url,args.model,prompt,128,102,7200); after=metrics(args.base_url)
    out={"before_metrics":before,"after_metrics":after,"cold":a,"warm":b,"same_prompt":True}; Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
