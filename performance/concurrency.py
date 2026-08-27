#!/usr/bin/env python3
"""Small concurrent request probe; use realistic mixed lengths rather than eight 1M requests."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
from pathlib import Path

from performance.throughput import one
from benchmarks.arro_longwriter.fixtures.common import build_fixture


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--base-url",default="http://127.0.0.1:8000"); ap.add_argument("--model",default="brainwaves-qwen38-27b"); ap.add_argument("--lengths",default="65536,65536,8192,8192"); ap.add_argument("--output-tokens",type=int,default=128); ap.add_argument("--output",default="results/aggregate/concurrency.json"); args=ap.parse_args()
    lengths=[int(x) for x in args.lengths.split(",") if x]; jobs=[(build_fixture(n,"narrative_continuation",101+i,0)["prompt"],101+i) for i,n in enumerate(lengths)]; start=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as ex: rows=list(ex.map(lambda x:one(args.base_url,args.model,x[0],args.output_tokens,x[1],7200),jobs))
    out={"concurrency":len(jobs),"lengths":lengths,"elapsed_s":time.perf_counter()-start,"rows":rows}; Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
