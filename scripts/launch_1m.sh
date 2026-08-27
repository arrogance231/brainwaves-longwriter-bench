#!/usr/bin/env bash
set -euo pipefail
PROFILE=yarn-1m exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/serving/vllm/start.sh"
