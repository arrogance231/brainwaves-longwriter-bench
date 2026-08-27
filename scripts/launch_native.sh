#!/usr/bin/env bash
set -euo pipefail
PROFILE=native-262k exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/serving/vllm/start.sh"
