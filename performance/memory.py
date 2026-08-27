#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results/aggregate/memory.json"); args=ap.parse_args()
    probes={}
    for name,cmd in {"rocm_smi":"rocm-smi --showmeminfo vram --showuse --json","free":"free -b","metrics":"curl -fsS http://127.0.0.1:8000/metrics"}.items():
        try:
            p=subprocess.run(cmd,shell=True,text=True,capture_output=True,timeout=20); probes[name]={"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
        except Exception as e: probes[name]={"error":repr(e)}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(probes,indent=2)+"\n"); print(json.dumps(probes,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
