#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODEL_DIR="${MODEL_DIR:-/models/Qwen3.8-27B-Brainwaves}"
MODEL_REVISION="${MODEL_REVISION:-f9545772aab3abcb84b2f1822134a1c4a052669f}"
VLLM_IMAGE="${VLLM_IMAGE:-vllm-rocm:0.28.0-gfx942}"
SGLANG_IMAGE="${SGLANG_IMAGE:-lmsysorg/sglang:dev-qwen38-27b-dflash2}"
CONTAINER_NAME="${CONTAINER_NAME:-brainwaves-vllm}"
HOST_BIND="${HOST_BIND:-127.0.0.1}"
PORT="${PORT:-8000}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-brainwaves-qwen38-27b}"
VLLM_ROCM_USE_AITER="${VLLM_ROCM_USE_AITER:-1}"
VLLM_ROCM_USE_AITER_RMSNORM="${VLLM_ROCM_USE_AITER_RMSNORM:-0}"
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:${PORT}}"

profile_file() {
  local profile="${1:-native-262k}"
  printf '%s/configs/%s.yaml' "$ROOT_DIR" "$profile"
}
