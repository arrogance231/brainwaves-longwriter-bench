#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../common" && pwd)/env.sh"
PROFILE="${PROFILE:-native-262k}"
PROFILE_FILE="$(profile_file "$PROFILE")"
[[ -f "$PROFILE_FILE" ]] || { echo "Unknown profile: $PROFILE" >&2; exit 2; }
MAX_MODEL_LEN="${MAX_MODEL_LEN:-$(python3 - "$PROFILE_FILE" <<'PY'
import sys
import yaml
print(yaml.safe_load(open(sys.argv[1]))["max_model_len"])
PY
)}"
ROPE_JSON="$(python3 - "$PROFILE_FILE" <<'PY'
import json
import sys
import yaml
data = yaml.safe_load(open(sys.argv[1])) or {}
print(json.dumps(data.get("rope"), separators=(",", ":")) if data.get("rope") else "")
PY
)"
ARGS=(python3 -m sglang.launch_server --model-path /models/Qwen3.8-27B-Brainwaves --host 0.0.0.0 --port 30000 --tp-size 1 --context-length "$MAX_MODEL_LEN" --reasoning-parser qwen3 --chunked-prefill-size "${CHUNKED_PREFILL_SIZE:-8192}" --mamba-ssm-dtype bfloat16)
if [[ -n "$ROPE_JSON" ]]; then
  JSON_OVERRIDE="$(python3 - "$ROPE_JSON" <<'PY'
import json
import sys
print(json.dumps({"text_config": {"rope_parameters": json.loads(sys.argv[1])}}, separators=(",", ":")))
PY
)"
  ARGS+=(--json-model-override-args "$JSON_OVERRIDE")
fi
[[ -n "${SGLANG_API_KEY:-}" ]] && ARGS+=(--api-key "$SGLANG_API_KEY")
DOCKER_ARGS=(
  run --rm --name "${SGLANG_CONTAINER_NAME:-brainwaves-sglang}"
  --device /dev/kfd --device /dev/dri --ipc=host --shm-size 32g
  --security-opt seccomp=unconfined -p "${SGLANG_HOST_BIND:-127.0.0.1}:30000:30000"
  -v "$MODEL_DIR:/models/Qwen3.8-27B-Brainwaves:ro" -v "$ROOT_DIR:/workspace:ro"
  -e SGLANG_USE_AITER="${SGLANG_USE_AITER:-1}" "$SGLANG_IMAGE" "${ARGS[@]}"
)
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  printf 'docker'
  printf ' %q' "${DOCKER_ARGS[@]}"
  printf '\n'
  exit 0
fi
echo "SGLang comparison is experimental; validate image and commit before reporting."
exec docker "${DOCKER_ARGS[@]}"
