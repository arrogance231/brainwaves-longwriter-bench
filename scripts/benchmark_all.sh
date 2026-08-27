#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
MODEL="${MODEL_NAME:-brainwaves-qwen38-27b}"
LENGTHS="${LENGTHS:-8192,32768,65536,131072,262144}"
if [[ "${ALLOW_ULTRA:-0}" == "1" ]]; then LENGTHS="${LENGTHS_ULTRA:-8192,32768,65536,131072,262144,393216,524288,768000,1010000}"; fi
python3 "$ROOT_DIR/benchmarks/arro_longwriter/run.py" --base-url "$BASE_URL" --model "$MODEL" --lengths "$LENGTHS" --scenarios "${SCENARIOS:-all}" --seeds "${SEEDS:-101}" --samples "${SAMPLES:-1}" --max-tokens "${MAX_TOKENS:-512}" --output "${OUTPUT:-$ROOT_DIR/results/raw/arro-matrix.jsonl}"
python3 "$ROOT_DIR/benchmarks/arro_longwriter/score.py" --input "${OUTPUT:-$ROOT_DIR/results/raw/arro-matrix.jsonl}" --output "${REPORT_JSON:-$ROOT_DIR/results/aggregate/arro-matrix.json}" --markdown "${REPORT_MD:-$ROOT_DIR/reports/FINAL_REPORT.md}"
