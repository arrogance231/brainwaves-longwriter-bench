#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../common" && pwd)/env.sh"

PROFILE="${PROFILE:-native-262k}"
PROFILE_FILE="$(profile_file "$PROFILE")"
[[ -f "$PROFILE_FILE" ]] || { echo "Unknown profile: $PROFILE" >&2; exit 2; }

read_yaml() {
  python3 - "$PROFILE_FILE" "$1" <<'PY'
import sys
import yaml
data = yaml.safe_load(open(sys.argv[1])) or {}
value = data
for part in sys.argv[2].split('.'):
    value = value.get(part) if isinstance(value, dict) else None
print("" if value is None else ("true" if value is True else "false" if value is False else value))
PY
}

MAX_MODEL_LEN="${MAX_MODEL_LEN:-$(read_yaml max_model_len)}"
KV_CACHE_DTYPE="${KV_CACHE_DTYPE:-$(read_yaml kv_cache_dtype)}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-$(read_yaml gpu_memory_utilization)}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-$(read_yaml max_num_seqs)}"
MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS:-$(read_yaml max_num_batched_tokens)}"
CHUNKED_PREFILL_SIZE="${CHUNKED_PREFILL_SIZE:-$(read_yaml chunked_prefill_size)}"
MAX_CUDAGRAPH_CAPTURE_SIZE="${MAX_CUDAGRAPH_CAPTURE_SIZE:-$(read_yaml max_cudagraph_capture_size)}"
MTP_ENABLED="${MTP_ENABLED:-$(read_yaml mtp)}"
ROPE_JSON="$(python3 - "$PROFILE_FILE" <<'PY'
import json
import sys
import yaml
data = yaml.safe_load(open(sys.argv[1])) or {}
print(json.dumps(data.get("rope"), separators=(",", ":")) if data.get("rope") else "")
PY
)"

[[ -d "$MODEL_DIR" ]] || { echo "Model directory not found: $MODEL_DIR" >&2; exit 1; }
GROUP_ARGS=()
for group in video render; do
  gid="$(getent group "$group" 2>/dev/null | cut -d: -f3 || true)"
  [[ -n "$gid" ]] && GROUP_ARGS+=(--group-add "$gid")
done
API_ARGS=()
if [[ -n "${VLLM_API_KEY:-}" ]]; then API_ARGS+=(--api-key "$VLLM_API_KEY"); fi
if [[ -n "${API_KEY_FILE:-}" ]]; then API_ARGS+=(--api-key "$(<"$API_KEY_FILE")"); fi

VLLM_ARGS=(
  serve /models/Qwen3.8-27B-Brainwaves
  --dtype bfloat16
  --served-model-name "$SERVED_MODEL_NAME"
  --host 0.0.0.0 --port 8000
  --tensor-parallel-size 1
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
  --max-num-seqs "$MAX_NUM_SEQS"
  --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS"
  --max-cudagraph-capture-size "$MAX_CUDAGRAPH_CAPTURE_SIZE"
  --kv-cache-dtype "$KV_CACHE_DTYPE"
  --enable-prefix-caching
  --enable-chunked-prefill
  --language-model-only
  --reasoning-parser qwen3
  --generation-config vllm
  "${API_ARGS[@]}"
)
if [[ "${MTP_ENABLED:-false}" == "true" ]]; then
  # Native Qwen MTP is optional and currently experimental on AMD in vLLM.
  VLLM_ARGS+=(--speculative-config '{"method":"mtp","num_speculative_tokens":2}')
fi
# vLLM 0.28 uses --max-num-batched-tokens as the chunk budget; newer builds
# may expose a separate --chunked-prefill-size flag. Keep the profile value in
# the environment for cross-runtime reporting without passing an unsupported
# option to this image.
if [[ -n "$ROPE_JSON" ]]; then
  HF_OVERRIDE="$(python3 - "$ROPE_JSON" <<'PY'
import json
import sys
print(json.dumps({"text_config": {"rope_parameters": json.loads(sys.argv[1])}}, separators=(",", ":")))
PY
)"
  VLLM_ARGS+=(--hf-overrides "$HF_OVERRIDE")
  export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
fi

DOCKER_ARGS=(
  run --rm --name "$CONTAINER_NAME"
  --device /dev/kfd --device /dev/dri "${GROUP_ARGS[@]}"
  --ipc=host --shm-size 32g --security-opt seccomp=unconfined --cap-add SYS_PTRACE
  -p "$HOST_BIND:$PORT:8000"
  -v "$MODEL_DIR:/models/Qwen3.8-27B-Brainwaves:ro"
  -v "$ROOT_DIR:/workspace:ro"
  -e PYTHONPATH=/workspace
  -e VLLM_ROCM_USE_AITER="$VLLM_ROCM_USE_AITER"
  -e VLLM_ROCM_USE_AITER_RMSNORM="$VLLM_ROCM_USE_AITER_RMSNORM"
  -e TORCH_BLAS_PREFER_HIPBLASLT=1
  -e SAFETENSORS_FAST_GPU=1
  -e VLLM_NO_USAGE_STATS=1
)
[[ -n "${VLLM_API_KEY:-}" ]] && DOCKER_ARGS+=(-e VLLM_API_KEY)
[[ -n "${HF_TOKEN:-}" ]] && DOCKER_ARGS+=(-e HF_TOKEN)
DOCKER_ARGS+=("$VLLM_IMAGE" "${VLLM_ARGS[@]}")

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  printf 'docker'
  printf ' %q' "${DOCKER_ARGS[@]}"
  printf '\n'
  exit 0
fi
exec docker "${DOCKER_ARGS[@]}"
