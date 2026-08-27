#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL_NAME:-brainwaves-qwen38-27b}"
curl -fsS "$BASE_URL/health" >/dev/null
curl -fsS "$BASE_URL/v1/models" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("data"), d; print(d["data"][0].get("id"))'
python3 - "$BASE_URL" "$MODEL" <<'PY'
import json,sys,requests
r=requests.post(sys.argv[1].rstrip('/')+'/v1/chat/completions',json={'model':sys.argv[2],'messages':[{'role':'user','content':'Write two original sentences about a rainy school corridor. Do not show reasoning.'}],'max_tokens':64,'temperature':0.8,'top_p':0.9,'top_k':20,'min_p':0.05,'presence_penalty':1.2,'seed':101,'chat_template_kwargs':{'enable_thinking':False}},timeout=(60,600)); r.raise_for_status(); d=r.json(); print(d['choices'][0]['message'].get('content',''))
PY
