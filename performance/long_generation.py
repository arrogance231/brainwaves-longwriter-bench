#!/usr/bin/env python3
"""Measure sustained prose decoding; raw text is written outside Git by default."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import requests
from benchmarks.arro_longwriter.fixtures.common import build_fixture

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='http://127.0.0.1:8000'); ap.add_argument('--model',default='brainwaves-qwen38-27b'); ap.add_argument('--context',type=int,default=8192); ap.add_argument('--max-tokens',type=int,default=2048); ap.add_argument('--instruction',default='Continue the scene in original prose.'); ap.add_argument('--output',default='results/aggregate/long-generation.json'); ap.add_argument('--raw-output',default='results/raw/long-generation.txt'); args=ap.parse_args()
    prompt=build_fixture(args.context,'narrative_continuation',101,0)['prompt'] + '\n\n' + args.instruction
    body={'model':args.model,'messages':[{'role':'user','content':prompt}], 'max_tokens':args.max_tokens,'temperature':0.8,'top_p':0.9,'top_k':20,'min_p':0.05,'presence_penalty':1.2,'seed':101,'stream':True,'stream_options':{'include_usage':True},'chat_template_kwargs':{'enable_thinking':False}}
    start=time.perf_counter(); first=None; parts=[]; usage={}
    with requests.post(args.base_url.rstrip('/')+'/v1/chat/completions',json=body,stream=True,timeout=(60,7200)) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data:'): continue
            payload=line[5:].strip()
            if payload=='[DONE]': continue
            try: d=json.loads(payload)
            except json.JSONDecodeError: continue
            if first is None: first=time.perf_counter()
            usage.update(d.get('usage') or {})
            for choice in d.get('choices') or []:
                c=(choice.get('delta') or {}).get('content')
                if c: parts.append(c)
    end=time.perf_counter(); text=''.join(parts); tokens=int(usage.get('completion_tokens') or 0)
    Path(args.raw_output).parent.mkdir(parents=True,exist_ok=True); Path(args.raw_output).write_text(text)
    row={'context_target_tokens':args.context,'prompt_tokens':usage.get('prompt_tokens'),'completion_tokens':tokens,'word_count':len(text.split()),'elapsed_s':end-start,'ttft_s':(first-start if first else None),'decode_tok_s':tokens/max(end-(first or end),1e-6),'usage':usage}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(row,indent=2)+'\n'); print(json.dumps(row,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
